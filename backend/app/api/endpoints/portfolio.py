from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Dict, Any
from ...db.supabase import get_supabase_client
from ...core.config import load_config, LEGAL_DISCLAIMER

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/portfolio")
@limiter.limit("30/minute")
async def get_portfolio(request: Request):
    """
    Get current portfolio state including positions, equity, and P/L.
    """
    try:
        supabase = get_supabase_client()
        
        # Fetch current positions
        positions_response = supabase.table("positions").select("*").execute()
        positions = positions_response.data if positions_response.data else []
        
        # Fetch current equity
        equity_response = supabase.table("equity").select("*").order("timestamp.desc").limit(1).execute()
        current_equity = equity_response.data[0] if equity_response.data else {"equity": 0, "timestamp": None}
        
        # Calculate total P/L
        total_pl = sum(float(pos.get("unrealized_pl", 0)) for pos in positions)
        
        return {
            "positions": positions,
            "current_equity": current_equity.get("equity", 0),
            "total_pl": total_pl,
            "timestamp": current_equity.get("timestamp"),
            "data_delay_minutes": 15,  # As per PRD requirement
            "disclaimer": LEGAL_DISCLAIMER
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 