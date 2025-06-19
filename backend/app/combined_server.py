#!/usr/bin/env python3
"""
Combined API server + background bot runner.
Runs both the FastAPI application and the trading bot in the same process.
"""
import os
import asyncio
import threading
import time
import logging
from pathlib import Path

# Setup logging before importing anything else
def setup_logging():
    """Setup logging for the combined server."""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    handlers = [logging.StreamHandler()]
    
    try:
        log_file = log_dir / 'combined.log'
        handlers.append(logging.FileHandler(log_file))
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create combined log file: {e}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

setup_logging()

import uvicorn
from backend.app.api.main import app
from backend.app.main import run_trading_cycle, setup_application

logger = logging.getLogger(__name__)

class BackgroundBot:
    """Background trading bot that runs in a separate thread."""
    
    def __init__(self, interval_seconds=300):  # 5 minutes default
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the background bot in a separate thread."""
        if self.running:
            logger.warning("Bot is already running")
            return
            
        logger.info(f"Starting background bot with {self.interval_seconds}s interval")
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the background bot."""
        logger.info("Stopping background bot")
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
            
    def _run_loop(self):
        """Main bot loop that runs in the background thread."""
        logger.info("Background bot loop started")
        
        # Initialize the application once
        try:
            setup_application()
            logger.info("Bot application setup completed")
        except Exception as e:
            logger.error(f"Bot setup failed: {e}")
            return
            
        # Main trading loop
        while self.running:
            try:
                logger.info("Running trading cycle...")
                run_trading_cycle("AAPL")  # Default symbol
                logger.info(f"Trading cycle completed, sleeping for {self.interval_seconds}s")
                
                # Sleep with interruption check
                for _ in range(self.interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retrying on error

# Global bot instance
background_bot = BackgroundBot()

@app.on_event("startup")
async def startup_event():
    """Start the background bot when the API server starts."""
    logger.info("API server starting, launching background bot...")
    background_bot.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background bot when the API server shuts down."""
    logger.info("API server shutting down, stopping background bot...")
    background_bot.stop()

def main():
    """Run the combined API server + background bot."""
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting combined API server + bot on {host}:{port}")
    print(f"Starting combined API server + bot on {host}:{port}")
    
    # Test basic app functionality
    try:
        print("Testing app import...")
        print(f"App routes: {len(app.routes)}")
        logger.info("Combined server initialized successfully")
    except Exception as e:
        print(f"Error initializing app: {e}")
        logger.error(f"Error initializing app: {e}")
        raise
    
    # Run the server
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