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
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.main import run_trading_cycle, setup_application
from backend.app.utils.helpers import is_market_open, get_time_until_market_open

logger = logging.getLogger(__name__)

class BackgroundBot:
    """Background trading bot that runs in a separate thread."""
    
    def __init__(self, interval_seconds=3600, symbols=None):  # 5 minutes default
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
        self.symbols = symbols or ["AAPL", "MSFT", "JNJ", "UNH", "V"]
        
    def start(self):
        """Start the background bot in a separate thread."""
        if self.running:
            logger.warning("Bot is already running")
            print("Bot is already running")
            return
            
        logger.info(f"Starting background bot with {self.interval_seconds}s interval")
        print(f"Starting background bot with {self.interval_seconds}s interval")
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Background bot thread started")
        print("Background bot thread started")
        
    def stop(self):
        """Stop the background bot."""
        logger.info("Stopping background bot")
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
            
    def _run_loop(self):
        """Main bot loop that runs in the background thread."""
        logger.info("=== BACKGROUND BOT LOOP STARTED ===")
        print("=== BACKGROUND BOT LOOP STARTED ===")
        
        # Initialize the application once
        try:
            logger.info("Setting up bot application...")
            print("Setting up bot application...")
            setup_application()
            logger.info("Bot application setup completed")
            print("Bot application setup completed")
        except Exception as e:
            logger.error(f"Bot setup failed: {e}", exc_info=True)
            print(f"Bot setup failed: {e}")
            return
            
        # Main trading loop
        while self.running:
            try:
                # Check if market is open
                if not is_market_open():
                    time_until_open = get_time_until_market_open()
                    hours_until_open = time_until_open // 3600
                    minutes_until_open = (time_until_open % 3600) // 60
                    
                    logger.info(f"Market is closed. Next open in {hours_until_open}h {minutes_until_open}m")
                    print(f"Market is closed. Next open in {hours_until_open}h {minutes_until_open}m")
                    
                    # Sleep for 30 minutes when market is closed (to avoid frequent checks)
                    sleep_time = min(1800, time_until_open)  # 30 minutes or time until open, whichever is shorter
                    logger.info(f"Sleeping for {sleep_time // 60} minutes while market is closed")
                    print(f"Sleeping for {sleep_time // 60} minutes while market is closed")
                    
                    # Sleep with interruption check
                    for _ in range(sleep_time):
                        if not self.running:
                            break
                        time.sleep(1)
                    continue
                
                # Market is open - run trading cycle
                if is_market_open():
                    logger.info("Market is open - running trading cycle for all symbols...")
                    print("Market is open - running trading cycle for all symbols...")
                    for symbol in self.symbols:
                        logger.info(f"Running trading cycle for {symbol}")
                        print(f"Running trading cycle for {symbol}")
                        run_trading_cycle(symbol)
                    logger.info(f"Trading cycles completed, sleeping for {self.interval_seconds}s")
                    print(f"Trading cycles completed, sleeping for {self.interval_seconds}s")
                
                # Sleep with interruption check
                for _ in range(self.interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                print(f"Error in bot loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying on error

# Global bot instance
background_bot = BackgroundBot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the background bot."""
    # Startup
    logger.info("API server starting, launching background bot...")
    print("API server starting, launching background bot...")
    background_bot.start()
    yield
    # Shutdown
    logger.info("API server shutting down, stopping background bot...")
    print("API server shutting down, stopping background bot...")
    background_bot.stop()

# Import base app and modify it to use our lifespan
from backend.app.api.main import app

# Add startup event to ensure bot starts
@app.on_event("startup")
async def startup_event():
    """Start the background bot when the API starts."""
    try:
        logger.info("=== STARTUP EVENT TRIGGERED ===")
        print("=== STARTUP EVENT TRIGGERED ===")
        logger.info("API server starting, launching background bot...")
        print("API server starting, launching background bot...")
        background_bot.start()
        logger.info("=== BACKGROUND BOT START CALLED ===")
        print("=== BACKGROUND BOT START CALLED ===")
    except Exception as e:
        logger.error(f"Error in startup event: {e}", exc_info=True)
        print(f"Error in startup event: {e}")
        raise

@app.on_event("shutdown") 
async def shutdown_event():
    """Stop the background bot when the API shuts down."""
    try:
        logger.info("=== SHUTDOWN EVENT TRIGGERED ===")
        print("=== SHUTDOWN EVENT TRIGGERED ===")
        logger.info("API server shutting down, stopping background bot...")
        print("API server shutting down, stopping background bot...")
        background_bot.stop()
    except Exception as e:
        logger.error(f"Error in shutdown event: {e}", exc_info=True)
        print(f"Error in shutdown event: {e}")

def main():
    """Run the combined API server + background bot."""
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting combined API server + bot on {host}:{port}")
    print(f"Starting combined API server + bot on {host}:{port}")
    
    # Start the background bot before starting the server
    logger.info("=== MANUALLY STARTING BACKGROUND BOT ===")
    print("=== MANUALLY STARTING BACKGROUND BOT ===")
    background_bot.start()
    
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

# Always call main() when this module is imported or executed
# This handles both direct execution and module execution (python -m)
if __name__ == "__main__" or __name__ == "backend.app.combined_server":
    main()