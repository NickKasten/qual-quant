from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import os
from typing import Dict, Any
from backend.app.utils.auth import verify_api_key, verify_api_key_optional

# Initialize FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="API for accessing trading bot portfolio, trades, and performance data. Protected endpoints require API key authentication via Bearer token.",
    version="1.0.0"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

# Health check endpoint
@app.get("/health")
@limiter.limit("5/minute")
async def health_check(request: Request):
    return {"status": "healthy", "timestamp": time.time()}

# Import and include routers
from .endpoints import portfolio, trades, performance, signals, status

app.include_router(portfolio.router, prefix="/api", tags=["portfolio"])
app.include_router(trades.router, prefix="/api", tags=["trades"])
app.include_router(performance.router, prefix="/api", tags=["performance"])
app.include_router(signals.router, prefix="/api", tags=["signals"])
app.include_router(status.router, prefix="/api", tags=["status"]) 