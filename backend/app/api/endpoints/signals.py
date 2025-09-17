from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict, Any
import pandas as pd

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore
    get_remote_address = None  # type: ignore

from ...db import supabase as supabase_db
from bot.strategy.signals import generate_signals
from ...services.fetcher import fetch_ohlcv
from ...core.config import LEGAL_DISCLAIMER
from ...utils.auth import verify_api_key

router = APIRouter()


class DummyLimiter:  # pragma: no cover - simple fallback
    def limit(self, *_args, **_kwargs):
        def decorator(func):
            return func

        return decorator


limiter = Limiter(key_func=get_remote_address) if Limiter and get_remote_address else DummyLimiter()
rate_limit = limiter.limit

@router.get("/signals")
@rate_limit("30/minute")
async def get_signals(request: Request, authenticated: bool = Depends(verify_api_key)):
    """
    Get current trading signals for all tracked symbols.
    """
    try:
        # Get list of symbols from positions table
        supabase = supabase_db.get_supabase_client()
        positions_response = supabase.table("positions").select("symbol").execute()
        symbols = [pos["symbol"] for pos in positions_response.data] if positions_response.data else []
        
        # Add default symbol if no positions
        if not symbols:
            symbols = ["AAPL"]  # Default symbol as per main.py
        
        signals_data = {}
        latest_timestamp = None
        
        for symbol in symbols:
            # Fetch latest OHLCV data
            ohlcv_data = fetch_ohlcv(symbol)
            if ohlcv_data is not None and not ohlcv_data.empty:
                # Generate signals
                signals = generate_signals(ohlcv_data)
                if signals:
                    # Extract latest technical indicators from the data
                    latest_data = signals['data'].iloc[-1]
                    
                    # Transform signal from integer to string
                    signal_map = {-1: "SELL", 0: "HOLD", 1: "BUY"}
                    signal_str = signal_map.get(signals['signal'], "HOLD")
                    
                    # Get current price
                    current_price = float(latest_data['close'])
                    
                    # Create conditions object
                    conditions = {}
                    if 'SMA20' in latest_data.index and 'SMA50' in latest_data.index:
                        sma20 = latest_data['SMA20']
                        sma50 = latest_data['SMA50']
                        if not (pd.isna(sma20) or pd.isna(sma50)):
                            conditions['sma_crossover'] = bool(sma20 > sma50) if signals['signal'] == 1 else bool(sma20 < sma50)
                    
                    if 'RSI' in latest_data.index:
                        rsi = latest_data['RSI']
                        if not pd.isna(rsi):
                            if signals['signal'] == 1:  # BUY
                                conditions['rsi_filter'] = bool(rsi < 70)
                            elif signals['signal'] == -1:  # SELL
                                conditions['rsi_filter'] = bool(rsi > 30)
                    
                    # Build response data
                    signals_data[symbol] = {
                        "signal": signal_str,
                        "sma_20": float(latest_data.get('SMA20', 0)) if not pd.isna(latest_data.get('SMA20')) else None,
                        "sma_50": float(latest_data.get('SMA50', 0)) if not pd.isna(latest_data.get('SMA50')) else None,
                        "rsi": float(latest_data.get('RSI', 0)) if not pd.isna(latest_data.get('RSI')) else None,
                        "current_price": current_price,
                        "conditions": conditions,
                        "strength": float(signals.get('strength', 0.5))
                    }
                    
                    # Update latest timestamp
                    if latest_timestamp is None:
                        latest_timestamp = ohlcv_data.index[-1].isoformat()
                else:
                    signals_data[symbol] = {"error": "Failed to generate signals"}
            else:
                signals_data[symbol] = {"error": "Failed to fetch OHLCV data"}
        
        return {
            "signals": signals_data,
            "timestamp": latest_timestamp,
            "data_delay_minutes": 15,  # As per PRD requirement
            "disclaimer": LEGAL_DISCLAIMER
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
