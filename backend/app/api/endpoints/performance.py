from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import Dict, Any, List, Optional

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore
    get_remote_address = None  # type: ignore

from ...db import supabase as supabase_db
from datetime import datetime, timedelta, timezone
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

@router.get("/performance")
@rate_limit("30/minute")
async def get_performance(request: Request, days: int = Query(30, ge=1, le=365, description="Number of days of performance data to return"), authenticated: bool = Depends(verify_api_key)):
    """
    Get equity curve data for performance analysis.
    """
    try:
        supabase = supabase_db.get_supabase_client()
        
        # Calculate start date
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Fetch equity data
        equity_response = (
            supabase.table("equity")
            .select("*")
            .gte("timestamp", start_date.isoformat())
            .order("timestamp.asc")
            .execute()
        )
        
        equity_data = equity_response.data if equity_response.data else []
        
        # Calculate performance metrics
        if equity_data:
            initial_equity = float(equity_data[0].get("equity", 0))
            final_equity = float(equity_data[-1].get("equity", 0))
            total_return = ((final_equity - initial_equity) / initial_equity * 100) if initial_equity > 0 else 0
        else:
            initial_equity = 0
            final_equity = 0
            total_return = 0
        
        return {
            "equity_curve": equity_data,
            "metrics": {
                "initial_equity": initial_equity,
                "final_equity": final_equity,
                "total_return_percent": total_return,
                "period_days": days
            },
            "data_delay_minutes": 15  # As per PRD requirement
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
