#!/usr/bin/env python3
"""
Production API server for the trading bot.
Serves the FastAPI application with uvicorn.
"""
import os
import uvicorn
from backend.app.api.main import app

def main():
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=1,
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()