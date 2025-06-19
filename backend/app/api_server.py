#!/usr/bin/env python3
"""
Production API server for the trading bot.
Serves the FastAPI application with uvicorn.
"""
import os
import logging
from pathlib import Path

# Setup logging before importing anything else
def setup_logging():
    """Setup logging for the API server."""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    handlers = [logging.StreamHandler()]
    
    try:
        log_file = log_dir / 'api.log'
        handlers.append(logging.FileHandler(log_file))
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create API log file: {e}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

setup_logging()

import uvicorn
from backend.app.api.main import app

def main():
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting API server on {host}:{port}")
    logging.info(f"Starting API server on {host}:{port}")
    
    # Test basic app functionality
    try:
        print("Testing app import...")
        print(f"App routes: {len(app.routes)}")
        logging.info("API server initialized successfully")
    except Exception as e:
        print(f"Error initializing app: {e}")
        logging.error(f"Error initializing app: {e}")
        raise
    
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