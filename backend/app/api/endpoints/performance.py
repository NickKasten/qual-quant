import logging
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
from ...core.config import LEGAL_DISCLAIMER, load_config
from ...services.fetcher import fetch_ohlcv
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


def _parse_timestamp(value: str) -> datetime:
    """Parse ISO timestamp strings with or without timezone suffix."""
    if value.endswith('Z'):
        value = value.replace('Z', '+00:00')
    return datetime.fromisoformat(value)


def _normalize_equity_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Coerce Supabase equity rows into consistent numeric structure."""
    normalized: List[Dict[str, Any]] = []
    for row in records:
        timestamp = row.get("timestamp")
        if not timestamp:
            continue
        normalized.append({
            "timestamp": timestamp,
            "equity": float(row.get("equity", 0) or 0),
            "cash": float(row.get("cash", 0) or 0)
        })
    return normalized

@router.get("/performance")
@rate_limit("30/minute")
async def get_performance(request: Request, days: int = Query(30, ge=1, le=365, description="Number of days of performance data to return"), authenticated: bool = Depends(verify_api_key)):
    """
    Get equity curve data for performance analysis.
    """
    try:
        config = load_config()
        starting_equity = float(config.get("STARTING_EQUITY", 100000))

        supabase = supabase_db.get_supabase_client()

        # Calculate start date for requested window
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Primary query scoped to requested window
        equity_query = (
            supabase.table("equity")
            .select("*")
            .gte("timestamp", start_date.isoformat())
            .order("timestamp", desc=False)
        )
        equity_response = equity_query.execute()
        equity_records = equity_response.data or []

        # Fallback: pull the most recent N records even if older than requested window
        if not equity_records:
            logger.info("No equity rows within requested window; falling back to most recent records")
            fallback_response = (
                supabase.table("equity")
                .select("*")
                .order("timestamp", desc=True)
                .limit(days)
                .execute()
            )
            fallback_records = fallback_response.data or []
            fallback_records.reverse()  # Ensure chronological order
            equity_records = fallback_records

        equity_data = _normalize_equity_records(equity_records)

        if equity_data:
            initial_equity = equity_data[0]["equity"]
            final_equity = equity_data[-1]["equity"]
            total_return = ((final_equity - initial_equity) / initial_equity * 100) if initial_equity > 0 else 0
            latest_timestamp = _parse_timestamp(equity_data[-1]["timestamp"])
            data_delay_minutes = max(0, int((datetime.now(timezone.utc) - latest_timestamp).total_seconds() // 60))
        else:
            initial_equity = starting_equity
            final_equity = starting_equity
            total_return = 0
            data_delay_minutes = 15

        benchmark_curve: List[Dict[str, Any]] = []
        benchmark_metrics: Optional[Dict[str, Any]] = None
        benchmark_symbol = "SPY"

        try:
            market_df = fetch_ohlcv(benchmark_symbol)
            if market_df is not None and not market_df.empty and equity_data:
                market_df = market_df.sort_index()
                price_series = market_df['close'] if 'close' in market_df.columns else None

                if price_series is not None and not price_series.empty:
                    # Build price lookup by date for easy joins
                    price_lookup = {idx.date(): float(price) for idx, price in price_series.items() if price is not None}

                    # Use the first equity date as normalization anchor
                    equity_start_dt = _parse_timestamp(equity_data[0]['timestamp'])
                    benchmark_start_price = price_lookup.get(equity_start_dt.date())

                    if benchmark_start_price is None:
                        # Fallback: use earliest available price
                        first_entry = next(iter(price_lookup.values()), None)
                        benchmark_start_price = float(first_entry) if first_entry is not None else None

                    if benchmark_start_price:
                        benchmark_points: List[Dict[str, Any]] = []
                        for point in equity_data:
                            point_dt = _parse_timestamp(point['timestamp']).date()
                            benchmark_price = price_lookup.get(point_dt)
                            if benchmark_price is None:
                                continue
                            normalized_equity = (benchmark_price / benchmark_start_price) * initial_equity
                            benchmark_points.append({
                                "timestamp": point['timestamp'],
                                "equity": normalized_equity,
                                "price": benchmark_price
                            })

                        if benchmark_points:
                            benchmark_curve = benchmark_points
                            benchmark_initial = benchmark_points[0]['equity']
                            benchmark_final = benchmark_points[-1]['equity']
                            benchmark_return = ((benchmark_final - benchmark_initial) / benchmark_initial * 100) if benchmark_initial > 0 else 0
                            benchmark_metrics = {
                                "initial_equity": benchmark_initial,
                                "final_equity": benchmark_final,
                                "total_return_percent": benchmark_return,
                                "period_days": len(benchmark_points)
                            }
        except Exception as benchmark_error:
            logger.warning("Benchmark data unavailable: %s", benchmark_error)

        return {
            "equity_curve": equity_data,
            "metrics": {
                "initial_equity": initial_equity,
                "final_equity": final_equity,
                "total_return_percent": total_return,
                "period_days": days
            },
            "benchmark_symbol": benchmark_symbol,
            "benchmark_curve": benchmark_curve,
            "benchmark_metrics": benchmark_metrics,
            "data_delay_minutes": data_delay_minutes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
