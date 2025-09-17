from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import Dict, Any, List, Optional
import logging

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore
    get_remote_address = None  # type: ignore

from ...db import supabase as supabase_db
from ...core.config import LEGAL_DISCLAIMER
from ...utils.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


class DummyLimiter:  # pragma: no cover - simple fallback
    def limit(self, *_args, **_kwargs):
        def decorator(func):
            return func

        return decorator


limiter = Limiter(key_func=get_remote_address) if Limiter and get_remote_address else DummyLimiter()
rate_limit = limiter.limit

@router.get("/trades")
@rate_limit("30/minute")
async def get_trades(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get trade history with pagination and optional symbol filter.
    """
    try:
        supabase = supabase_db.get_supabase_client()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count using a separate query
        # Note: Supabase Python client v1.0.3 has issues with count parameter
        # Using a workaround by fetching all IDs and counting them
        count_query = supabase.table("trades").select("id")
        
        # Apply symbol filter if provided for count
        if symbol:
            count_query = count_query.eq("symbol", symbol)
        
        # Get total count by fetching all records and counting
        try:
            count_response = count_query.execute()
            total_count = len(count_response.data) if count_response.data else 0
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            total_count = 0
        
        # Build query for data retrieval
        data_query = supabase.table("trades").select("*")
        
        # Apply symbol filter if provided for data
        if symbol:
            data_query = data_query.eq("symbol", symbol)
        
        # Get paginated results
        trades_response = (
            data_query
            .order("timestamp.desc")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        
        trades = trades_response.data if trades_response.data else []
        
        return {
            "trades": trades,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            },
            "data_delay_minutes": 15,  # As per PRD requirement
            "disclaimer": LEGAL_DISCLAIMER
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
