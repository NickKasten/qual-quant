from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict, Any
from ...db import supabase as supabase_db
from datetime import datetime, timezone
from ...core.config import LEGAL_DISCLAIMER
from ...utils.auth import verify_api_key

router = APIRouter()

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore
    get_remote_address = None  # type: ignore


class DummyLimiter:  # pragma: no cover - simple fallback
    def limit(self, *_args, **_kwargs):
        def decorator(func):
            return func

        return decorator


limiter = Limiter(key_func=get_remote_address) if Limiter and get_remote_address else DummyLimiter()
rate_limit = limiter.limit


def build_status_payload() -> Dict[str, Any]:
    """Collect service health information for status endpoints."""
    supabase = supabase_db.get_supabase_client()

    db_status = "healthy"
    try:
        supabase.table("equity").select("id").limit(1).execute()
    except Exception:
        db_status = "unhealthy"

    latest_data = (
        supabase.table("equity")
        .select("timestamp")
        .order("timestamp.desc")
        .limit(1)
        .execute()
    )

    latest_timestamp = latest_data.data[0]["timestamp"] if latest_data.data else None

    if latest_timestamp:
        delay = datetime.now(timezone.utc) - datetime.fromisoformat(latest_timestamp)
        delay_minutes = int(delay.total_seconds() / 60)
    else:
        delay_minutes = None

    return {
        "status": {
            "database": db_status,
            "api": "healthy"
        },
        "data_delay_minutes": delay_minutes,
        "last_update": latest_timestamp,
        "system_time": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "disclaimer": LEGAL_DISCLAIMER
    }

@router.get("/status")
@rate_limit("30/minute")
async def get_status(request: Request, authenticated: bool = Depends(verify_api_key)):
    """
    Get system status and data delay information.
    """
    try:
        return build_status_payload()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
