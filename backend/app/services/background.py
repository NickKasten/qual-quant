"""
Background trading bot service.
Extracted from combined_server.py to make it a reusable service.
"""
import os
import time
import signal
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from ..core.logging import get_logger
from ..main import setup_application, run_trading_cycle
from ..utils.helpers import is_market_open, get_time_until_market_open


# Global status for health checks and monitoring
bot_status = {
    'status': 'starting',
    'cycles_completed': 0,
    'last_cycle_time': None,
    'uptime_start': datetime.now(timezone.utc),
    'market_open': False,
    'next_cycle_time': None
}

# Global flag for graceful shutdown
shutdown_flag = False


class BackgroundBot:
    """Background trading bot that runs in a separate thread."""
    
    def __init__(self, interval_seconds: int = 3600, symbols: Optional[List[str]] = None):
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
        self.symbols = symbols or ["AAPL", "MSFT", "JNJ", "UNH", "V"]
        self.logger = get_logger(__name__)
        
    def start(self):
        """Start the background bot in a separate thread."""
        if self.running:
            self.logger.warning("Bot is already running")
            return
            
        self.logger.info(f"Starting background bot with {self.interval_seconds}s interval")
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.logger.info("Background bot thread started")
        
    def stop(self):
        """Stop the background bot."""
        self.logger.info("Stopping background bot")
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
            
    def _run_loop(self):
        """Main bot loop that runs in the background thread."""
        self.logger.info("=== BACKGROUND BOT LOOP STARTED ===")
        
        # Initialize the application once
        try:
            self.logger.info("Setting up bot application...")
            setup_application()
            self.logger.info("Bot application setup completed")
        except Exception as e:
            self.logger.error(f"Bot setup failed: {e}", exc_info=True)
            return
            
        # Main trading loop
        while self.running:
            try:
                # Check if market is open
                if not is_market_open():
                    time_until_open = get_time_until_market_open()
                    hours_until_open = time_until_open // 3600
                    minutes_until_open = (time_until_open % 3600) // 60
                    
                    self.logger.info(f"Market is closed. Next open in {hours_until_open}h {minutes_until_open}m")
                    
                    # Sleep for 30 minutes when market is closed (to avoid frequent checks)
                    sleep_time = min(1800, time_until_open)  # 30 minutes or time until open, whichever is shorter
                    self.logger.info(f"Sleeping for {sleep_time // 60} minutes while market is closed")
                    
                    # Sleep with interruption check
                    for _ in range(sleep_time):
                        if not self.running:
                            break
                        time.sleep(1)
                    continue
                
                # Market is open - run trading cycle
                if is_market_open():
                    self.logger.info("Market is open - running trading cycle for all symbols...")
                    for symbol in self.symbols:
                        self.logger.info(f"Running trading cycle for {symbol}")
                        run_trading_cycle(symbol)
                    self.logger.info(f"Trading cycles completed, sleeping for {self.interval_seconds}s")
                
                # Sleep with interruption check
                for _ in range(self.interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retrying on error


# Global bot instance
background_bot = BackgroundBot()


def signal_handler(signum, _frame):
    """Handle shutdown signals from deployment platforms."""
    global shutdown_flag, background_bot
    logger = get_logger(__name__)
    logger.info(f"🛑 Received signal {signum} - initiating graceful shutdown")
    
    # Update status for health checks
    bot_status['status'] = 'shutting_down'
    shutdown_flag = True
    
    # Stop background bot
    background_bot.stop()


def run_background_bot_loop(symbols: str = "AAPL,MSFT,JNJ,UNH,V",
                           interval: int = 3600,
                           max_loops: Optional[int] = None):
    """
    Run the background bot main loop (for standalone bot mode).
    
    Args:
        symbols: Comma-separated trading symbols
        interval: Trading cycle interval in seconds
        max_loops: Maximum number of cycles (for testing)
    """
    logger = get_logger(__name__)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup application
    setup_application()
    
    start_time = datetime.now(timezone.utc)
    cycle_count = 0
    
    # Update bot status
    bot_status['status'] = 'running'
    
    logger.info("=" * 60)
    logger.info("🚀 TRADING BOT BACKGROUND WORKER STARTING")
    logger.info(f"📊 Symbols: {symbols}")
    
    symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    
    while not shutdown_flag:
        try:
            current_time = datetime.now(timezone.utc)
        
            # Check if market is open
            market_open = is_market_open()
            bot_status['market_open'] = market_open
            logger.info(f"🏪 Market status: {'OPEN' if market_open else 'CLOSED'} at {current_time.strftime('%H:%M:%S UTC')}")
            
            if not market_open:
                time_until_open = get_time_until_market_open()
                hours_until_open = time_until_open // 3600
                minutes_until_open = (time_until_open % 3600) // 60
                
                logger.info(f"🕐 Market closed - Next open in {hours_until_open}h {minutes_until_open}m")
                
                # Sleep for 30 minutes when market is closed (to avoid frequent checks)
                sleep_time = min(1800, time_until_open)  # 30 minutes or time until open
                sleep_minutes = sleep_time // 60
                
                logger.info(f"😴 Sleeping for {sleep_minutes} minutes while market is closed")
                
                # Interruptible sleep for market closed period
                for _ in range(sleep_time):
                    if shutdown_flag:
                        break
                    time.sleep(1)
                continue
            
            # Market is open - run trading cycle
            cycle_count += 1
            bot_status['cycles_completed'] = cycle_count
            
            logger.info("=" * 40)
            logger.info(f"📈 TRADING CYCLE #{cycle_count} STARTING")
            logger.info(f"📊 Symbols: {symbols}")
            logger.info(f"🕐 Time: {current_time.strftime('%H:%M:%S UTC')}")
            logger.info("=" * 40)
            
            for symbol in symbol_list:
                logger.info(f"📈 Running trading cycle #{cycle_count} for {symbol}")
                run_trading_cycle(symbol)
            
            bot_status['last_cycle_time'] = current_time
            logger.info(f"✅ Trading cycle #{cycle_count} completed")
            
            # Log next cycle info
            next_cycle_time = current_time.timestamp() + interval
            next_cycle_datetime = datetime.fromtimestamp(next_cycle_time, timezone.utc)
            next_cycle_str = next_cycle_datetime.strftime('%H:%M:%S UTC')
            bot_status['next_cycle_time'] = next_cycle_datetime
            
            logger.info(f"⏳ Next cycle #{cycle_count + 1} at {next_cycle_str}")
            logger.info(f"😴 Sleeping for {interval}s ({interval//60} minutes)")
            
            if max_loops is not None and cycle_count >= max_loops:
                logger.info(f"🏁 Reached max loops limit: {max_loops}")
                break
            
            # Interruptible sleep for trading interval
            for _ in range(interval):
                if shutdown_flag:
                    break
                time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("⌨️  Keyboard interrupt received - shutting down bot")
            break
        except Exception as e:
            logger.error(f"❌ Error in bot loop: {e}", exc_info=True)
            
            # Wait 1 minute before retrying on error
            logger.info("⏳ Waiting 60 seconds before retry...")
            time.sleep(60)
        
    # Log final stats
    runtime = datetime.now(timezone.utc) - start_time
    logger.info("=" * 60)
    logger.info("🏁 TRADING BOT BACKGROUND WORKER SHUTDOWN")
    logger.info(f"📈 Total runtime: {runtime}")
    logger.info(f"🔄 Total cycles completed: {cycle_count}")
    logger.info("=" * 60)