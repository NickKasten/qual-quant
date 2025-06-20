import time
import logging
import argparse
import sys
import os
import signal
from pathlib import Path
from datetime import datetime, timezone
from backend.app.services.fetcher import fetch_ohlcv
from bot.strategy.signals import generate_signals
from bot.risk.risk import calculate_position_size
from backend.app.services.broker.paper import execute_trade
from backend.app.db.supabase import update_trades, update_positions, update_equity
from backend.app.core.config import load_config
from backend.app.utils.helpers import log_function_call, exponential_backoff, is_market_open, get_time_until_market_open
from backend.app.db.init_db import init_database

# Configure logging with proper error handling
def setup_logging():
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
    
    handlers = [logging.StreamHandler()]
    
    # Only add file handler if we can write to the logs directory
    try:
        log_file = log_dir / 'trading.log'
        handlers.append(logging.FileHandler(log_file))
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create log file: {e}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

setup_logging()
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(signum, frame):
    """Handle shutdown signals from Render."""
    global shutdown_flag
    logger.info(f"🛑 Received signal {signum} - initiating graceful shutdown")
    print(f"🛑 Received shutdown signal - stopping bot gracefully")
    shutdown_flag = True

# Register signal handlers for Render deployment
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def setup_application():
    """Initialize application components."""
    try:
        # Load configuration
        settings = load_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize database
        if not init_database():
            logger.error("Failed to initialize database")
            sys.exit(1)
        logger.info("Database initialized successfully")
        
        return settings
    except Exception as e:
        logger.error(f"Application setup failed: {e}", exc_info=True)
        sys.exit(1)

@log_function_call
@exponential_backoff(max_retries=3, base_delay=1)
def run_trading_cycle(symbol: str = "AAPL"):
    try:
        # Load configuration
        settings = load_config()
        logger.info("Configuration loaded successfully")

        # Fetch OHLCV data
        data = fetch_ohlcv(symbol)
        if data is None or not hasattr(data, 'empty') or data.empty:
            logger.error("Failed to fetch OHLCV data or data is empty")
            return

        # Generate trading signals
        signals = generate_signals(data)
        if not signals:
            logger.info("No signals generated")
            return

        # Get current equity and open positions from DB or config
        current_equity = float(settings["STARTING_EQUITY"])
        open_positions = 0  # TODO: fetch from DB if available

        # Calculate position size based on risk
        position_size = calculate_position_size(signals, current_equity, open_positions)
        if not position_size:
            logger.info("No position size calculated")
            return

        # Determine trade side from signals
        side = signals.get('side', 'buy')

        # Execute simulated trade
        trade_result = execute_trade(position_size, symbol=symbol, side=side, simulate=True)
        if not trade_result:
            logger.error("Failed to execute trade")
            return

        # Update database with trade, positions, and equity
        update_trades(trade_result)
        update_positions(trade_result)
        update_equity(trade_result)

        logger.info("Trading cycle completed successfully")
    except Exception as e:
        logger.error(f"Error in trading cycle: {e}", exc_info=True)

def main():
    # Setup application
    settings = setup_application()
    
    parser = argparse.ArgumentParser(description="AI Trading Bot Main Loop")
    parser.add_argument('--symbol', type=str, default=os.environ.get("TRADING_SYMBOL", "AAPL"), help="Ticker symbol to trade")
    parser.add_argument('--loop', action='store_true', help="Run in infinite loop mode (default: single run)")
    parser.add_argument('--max-loops', type=int, default=None, help="Maximum number of loop iterations (for testing)")
    parser.add_argument('--interval', type=int, default=int(os.environ.get("TRADING_INTERVAL", "300")), help="Interval between trading cycles in seconds (default: 300)")
    args = parser.parse_args()

    if args.loop:
        start_time = datetime.now(timezone.utc)
        cycle_count = 0
        
        logger.info("=" * 60)
        logger.info("🚀 TRADING BOT BACKGROUND WORKER STARTING")
        logger.info(f"📊 Symbol: {args.symbol}")
        logger.info(f"⏱️  Interval: {args.interval}s ({args.interval//60} minutes)")
        logger.info(f"🕐 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("=" * 60)
        
        print("🚀 Trading Bot Background Worker Starting...")
        print(f"📊 Trading Symbol: {args.symbol}")
        print(f"⏱️  Check Interval: {args.interval//60} minutes")
        
        while not shutdown_flag:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Check if market is open
                market_open = is_market_open()
                logger.info(f"🏪 Market status: {'OPEN' if market_open else 'CLOSED'} at {current_time.strftime('%H:%M:%S UTC')}")
                
                if not market_open:
                    time_until_open = get_time_until_market_open()
                    hours_until_open = time_until_open // 3600
                    minutes_until_open = (time_until_open % 3600) // 60
                    
                    logger.info(f"🕐 Market closed - Next open in {hours_until_open}h {minutes_until_open}m")
                    print(f"🕐 Market closed - Next open in {hours_until_open}h {minutes_until_open}m")
                    
                    # Sleep for 30 minutes when market is closed (to avoid frequent checks)
                    sleep_time = min(1800, time_until_open)  # 30 minutes or time until open
                    sleep_minutes = sleep_time // 60
                    
                    logger.info(f"😴 Sleeping for {sleep_minutes} minutes while market is closed")
                    print(f"😴 Sleeping for {sleep_minutes} minutes while market is closed")
                    
                    # Interruptible sleep for market closed period
                    for _ in range(sleep_time):
                        if shutdown_flag:
                            break
                        time.sleep(1)
                    continue
                
                # Market is open - run trading cycle
                cycle_count += 1
                logger.info("=" * 40)
                logger.info(f"📈 TRADING CYCLE #{cycle_count} STARTING")
                logger.info(f"📊 Symbol: {args.symbol}")
                logger.info(f"🕐 Time: {current_time.strftime('%H:%M:%S UTC')}")
                logger.info("=" * 40)
                
                print(f"📈 Running trading cycle #{cycle_count} for {args.symbol}")
                
                run_trading_cycle(args.symbol)
                
                logger.info(f"✅ Trading cycle #{cycle_count} completed")
                print(f"✅ Trading cycle #{cycle_count} completed")
                
                # Log next cycle info
                next_cycle_time = current_time.timestamp() + args.interval
                next_cycle_str = datetime.fromtimestamp(next_cycle_time, timezone.utc).strftime('%H:%M:%S UTC')
                
                logger.info(f"⏳ Next cycle #{cycle_count + 1} at {next_cycle_str}")
                logger.info(f"😴 Sleeping for {args.interval}s ({args.interval//60} minutes)")
                print(f"⏳ Next cycle in {args.interval//60} minutes at {next_cycle_str}")
                
                if args.max_loops is not None and cycle_count >= args.max_loops:
                    logger.info(f"🏁 Reached max loops limit: {args.max_loops}")
                    break
                
                # Interruptible sleep for trading interval
                for _ in range(args.interval):
                    if shutdown_flag:
                        break
                    time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("⌨️  Keyboard interrupt received - shutting down bot")
                print("⌨️  Keyboard interrupt received - shutting down bot")
                break
            except Exception as e:
                logger.error(f"❌ Error in bot loop: {e}", exc_info=True)
                print(f"❌ Error in bot loop: {e}")
                
                # Wait 1 minute before retrying on error
                logger.info("⏳ Waiting 60 seconds before retry...")
                print("⏳ Waiting 60 seconds before retry...")
                time.sleep(60)
        
        # Log final stats
        runtime = datetime.now(timezone.utc) - start_time
        logger.info("=" * 60)
        logger.info("🏁 TRADING BOT BACKGROUND WORKER SHUTDOWN")
        logger.info(f"📈 Total runtime: {runtime}")
        logger.info(f"🔄 Total cycles completed: {cycle_count}")
        logger.info("=" * 60)
        print(f"🏁 Bot shutdown - Ran for {runtime}, completed {cycle_count} cycles")
        
    else:
        run_trading_cycle(args.symbol)

if __name__ == "__main__":
    main() 