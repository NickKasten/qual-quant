from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Dict, Any
from ...db.supabase import get_supabase_client
from bot.strategy.signals import generate_signals
from ...services.fetcher import fetch_ohlcv

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/signals")
@limiter.limit("30/minute")
async def get_signals(request: Request):
    """
    Get current trading signals for all tracked symbols.
    """
    try:
        # Get list of symbols from positions table
        supabase = get_supabase_client()
        positions_response = supabase.table("positions").select("symbol").execute()
        symbols = [pos["symbol"] for pos in positions_response.data] if positions_response.data else []
        
        # Add default symbol if no positions
        if not symbols:
            symbols = ["AAPL"]  # Default symbol as per main.py
        
        signals_data = {}
        for symbol in symbols:
            # Fetch latest OHLCV data
            ohlcv_data = fetch_ohlcv(symbol)
            if ohlcv_data is not None and not ohlcv_data.empty:
                # Generate signals
                signals = generate_signals(ohlcv_data)
                signals_data[symbol] = signals
            else:
                signals_data[symbol] = {"error": "Failed to fetch OHLCV data"}
        
        return {
            "signals": signals_data,
            "timestamp": ohlcv_data.index[-1].isoformat() if ohlcv_data is not None and not ohlcv_data.empty else None,
            "data_delay_minutes": 15  # As per PRD requirement
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 