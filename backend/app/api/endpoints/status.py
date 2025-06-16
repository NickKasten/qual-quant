from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Dict, Any
from ...db.supabase import get_supabase_client
from datetime import datetime, timedelta, UTC

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/status")
@limiter.limit("30/minute")
async def get_status(request: Request):
    """
    Get system status and data delay information.
    """
    try:
        supabase = get_supabase_client()
        
        # Check database connection
        db_status = "healthy"
        try:
            supabase.table("equity").select("count").limit(1).execute()
        except Exception:
            db_status = "unhealthy"
        
        # Get latest data timestamp
        latest_data = (
            supabase.table("equity")
            .select("timestamp")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        
        latest_timestamp = latest_data.data[0]["timestamp"] if latest_data.data else None
        
        # Calculate data delay
        if latest_timestamp:
            delay = datetime.now(UTC) - datetime.fromisoformat(latest_timestamp)
            delay_minutes = int(delay.total_seconds() / 60)
        else:
            delay_minutes = None
        
        return {
            "status": {
                "database": db_status,
                "api": "healthy",
                "data_delay_minutes": delay_minutes
            },
            "last_update": latest_timestamp,
            "system_time": datetime.now(UTC).isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 