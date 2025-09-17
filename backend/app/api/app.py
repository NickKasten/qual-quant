"""
FastAPI application factory.
Creates and configures the FastAPI app instance with all middleware and routes.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore
    _rate_limit_exceeded_handler = None  # type: ignore
    get_remote_address = None  # type: ignore
    RateLimitExceeded = None  # type: ignore


class DummyLimiter:  # pragma: no cover - simple fallback
    """Minimal limiter stub used when slowapi is unavailable."""

    def limit(self, *_args, **_kwargs):
        def decorator(func):
            return func

        return decorator


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application instance.
    
    Returns:
        Configured FastAPI app
    """
    # Initialize FastAPI app
    app = FastAPI(
        title="Trading Bot API",
        description="API for accessing trading bot portfolio, trades, and performance data. Protected endpoints require API key authentication via Bearer token.",
        version="1.0.0"
    )

    if Limiter and get_remote_address and RateLimitExceeded and _rate_limit_exceeded_handler:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    else:
        limiter = DummyLimiter()
        app.state.limiter = limiter

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global error handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "timestamp": time.time()}
        )

    # Root endpoint
    @app.get("/")
    async def root():
        return {"message": "Trading Bot API", "version": "1.0.0", "status": "running"}

    def _health_payload() -> dict:
        return {"status": "healthy", "timestamp": time.time()}

    # Health check endpoint with optional rate limiting
    @app.get("/health")  # type: ignore[misc]
    @limiter.limit("5/minute")  # type: ignore[call-arg]
    async def health_check(request: Request):  # pragma: no cover - dynamic definition
        return _health_payload()

    # Import and include routers
    from .endpoints import portfolio, trades, performance, signals, status

    @app.get("/status")
    async def public_status():
        return status.build_status_payload()

    app.include_router(portfolio.router, prefix="/api", tags=["portfolio"])
    app.include_router(trades.router, prefix="/api", tags=["trades"])
    app.include_router(performance.router, prefix="/api", tags=["performance"])
    app.include_router(signals.router, prefix="/api", tags=["signals"])
    app.include_router(status.router, prefix="/api", tags=["status"])
    
    return app
