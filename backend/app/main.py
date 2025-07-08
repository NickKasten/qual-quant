import time
import logging
import argparse
import sys
import os
import signal
import threading
from pathlib import Path
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from backend.app.services.fetcher import fetch_ohlcv
from bot.strategy.signals import generate_signals
from bot.risk.risk import calculate_position_size
from backend.app.services.broker.paper import execute_trade
from backend.app.db.supabase import update_trades, update_positions, update_equity, update_signals
from backend.app.core.config import load_config
from backend.app.utils.helpers import log_function_call, exponential_backoff, is_market_open, get_time_until_market_open
from backend.app.utils.monitoring import monitor
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

# Global status for health checks
bot_status = {
    'status': 'starting',
    'cycles_completed': 0,
    'last_cycle_time': None,
    'uptime_start': datetime.now(timezone.utc),
    'market_open': False,
    'next_cycle_time': None
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Render health checks."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        try:
            if self.path == '/health':
                # Health check endpoint
                uptime = datetime.now(timezone.utc) - bot_status['uptime_start']
                
                response = {
                    'status': 'healthy',
                    'bot_status': bot_status['status'],
                    'uptime_seconds': int(uptime.total_seconds()),
                    'cycles_completed': bot_status['cycles_completed'],
                    'market_open': bot_status['market_open'],
                    'last_cycle_time': bot_status['last_cycle_time'].isoformat() if bot_status['last_cycle_time'] else None,
                    'next_cycle_time': bot_status['next_cycle_time'].isoformat() if bot_status['next_cycle_time'] else None
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            elif self.path == '/':
                # Root endpoint
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Trading Bot is running')
                
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format_str, *args):
        """Suppress default HTTP logging to avoid log spam."""
        pass

def start_health_server(port=8080):
    """Start health check server in background thread."""
    global health_server
    try:
        health_server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🌐 Health check server starting on port {port}")
        health_server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")

# Global health server instance
health_server = None

def signal_handler(signum, _frame):
    """Handle shutdown signals from Render."""
    global shutdown_flag, health_server
    logger.info(f"🛑 Received signal {signum} - initiating graceful shutdown")
    print(f"🛑 Received shutdown signal - stopping bot gracefully")
    
    # Update status for health checks
    bot_status['status'] = 'shutting_down'
    
    shutdown_flag = True
    
    # Shutdown health server
    if health_server:
        try:
            health_server.shutdown()
            logger.info("🌐 Health server stopped")
        except Exception as e:
            logger.error(f"Error stopping health server: {e}")

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
            error_msg = "No market data available (all sources failed or returned empty data)"
            logger.info(f"⏭️  Trading cycle skipped: {error_msg}")
            monitor.record_failure(error_msg)
            return

        # Get current equity and open positions from DB first (needed for signal generation)
        current_equity = float(settings["STARTING_EQUITY"])
        
        # Fetch current positions from database
        from backend.app.db.operations import DatabaseOperations
        db_ops = DatabaseOperations()
        current_positions = db_ops.get_positions()
        open_positions = len(current_positions)
        
        # Get current position for this symbol (if any)
        existing_position = None
        existing_position_qty = 0
        for pos in current_positions:
            if pos.symbol == symbol:
                existing_position = pos
                existing_position_qty = pos.quantity
                break
        
        logger.info(f"Current positions: {open_positions}, Existing {symbol} position: {existing_position_qty}")

        # Generate trading signals with position awareness
        signals = generate_signals(data, existing_position=existing_position_qty)
        if not signals:
            logger.info("No signals generated")
            return

        # Store signals to database
        current_price = float(data['close'].iloc[-1]) if not data.empty else 100.0
        signal_data = {
            'symbol': symbol,
            'signal_type': signals.get('side', 'hold'),
            'strength': float(signals.get('strength', 0.5)),  # Convert numpy types to Python types
            'strategy': 'SMA_RSI',
            'price': current_price
        }
        
        # Log signal details for debugging
        logger.info(f"Generated signal: {signals.get('side')} with strength {signals.get('strength')}")
        if signals.get('used_fallback'):
            logger.info("Used fallback strategy due to insufficient data")
        
        update_signals(signal_data)

        # Calculate position size based on risk
        current_price = data['close'].iloc[-1] if not data.empty else 100.0
        position_size_data = calculate_position_size(signals, current_equity, open_positions, current_price)
        if not position_size_data:
            logger.info("No position size calculated - hold signal or no trading opportunity")
            logger.info("Trading cycle completed successfully (hold)")
            monitor.record_success()
            return

        # Extract the actual position size value
        position_size = position_size_data['position_size']
        side = signals.get('side', 'buy')
        
        logger.info(f"Using position size: {position_size} shares for {side.upper()} trade")

        # VALIDATE TRADE BEFORE EXECUTION
        if side == 'sell':
            if not existing_position or existing_position.quantity <= 0:
                logger.warning(f"Cannot SELL {symbol}: No existing position to sell")
                logger.info("Trading cycle completed successfully (invalid sell prevented)")
                monitor.record_success()
                return
            
            if position_size > existing_position.quantity:
                logger.warning(f"Cannot SELL {position_size} shares: Only own {existing_position.quantity} shares")
                # Adjust to sell available quantity
                position_size = int(existing_position.quantity)
                logger.info(f"Adjusted SELL size to {position_size} shares (max available)")
        
        elif side == 'buy':
            # Check if we have enough cash for BUY trade
            required_cash = position_size * current_price
            # Get latest equity info
            equity_history = db_ops.get_equity_history()
            if equity_history:
                available_cash = equity_history[-1].cash
                if available_cash < required_cash:
                    logger.warning(f"Cannot BUY {position_size} shares: Need ${required_cash:.2f}, only have ${available_cash:.2f}")
                    logger.info("Trading cycle completed successfully (insufficient funds prevented)")
                    monitor.record_success()
                    return
        
        # Execute validated trade
        trade_result = execute_trade(position_size, symbol=symbol, side=side, simulate=True)
        if not trade_result:
            error_msg = "Failed to execute trade"
            logger.error(error_msg)
            monitor.record_failure(error_msg)
            return

        # Update database with trade, positions, and equity
        update_trades(trade_result)
        
        # UPDATE POSITIONS CORRECTLY BASED ON TRADE DIRECTION
        if side == 'buy':
            # BUY: Add to position (or create new position)
            if existing_position:
                # Update existing position with weighted average price
                total_shares = existing_position.quantity + trade_result['quantity']
                total_value = (existing_position.quantity * existing_position.average_entry_price) + (trade_result['quantity'] * trade_result['price'])
                new_avg_price = total_value / total_shares
                
                position_data = {
                    'symbol': trade_result['symbol'],
                    'quantity': total_shares,
                    'average_entry_price': new_avg_price,
                    'current_price': trade_result['price'],
                    'unrealized_pnl': (trade_result['price'] - new_avg_price) * total_shares,
                    'timestamp': trade_result['timestamp']
                }
                logger.info(f"Updating existing position: {total_shares} shares @ ${new_avg_price:.2f} avg")
            else:
                # Create new position
                position_data = {
                    'symbol': trade_result['symbol'],
                    'quantity': trade_result['quantity'],
                    'average_entry_price': trade_result['price'],
                    'current_price': trade_result['price'],
                    'unrealized_pnl': 0.0,
                    'timestamp': trade_result['timestamp']
                }
                logger.info(f"Creating new position: {trade_result['quantity']} shares @ ${trade_result['price']:.2f}")
            
            update_positions(position_data)
            
        elif side == 'sell':
            # SELL: Reduce position (or close completely)
            if existing_position:
                remaining_shares = existing_position.quantity - trade_result['quantity']
                
                if remaining_shares > 0:
                    # Partial sale - keep position with same avg price
                    position_data = {
                        'symbol': trade_result['symbol'],
                        'quantity': remaining_shares,
                        'average_entry_price': existing_position.average_entry_price,
                        'current_price': trade_result['price'],
                        'unrealized_pnl': (trade_result['price'] - existing_position.average_entry_price) * remaining_shares,
                        'timestamp': trade_result['timestamp']
                    }
                    update_positions(position_data)
                    logger.info(f"Reduced position to {remaining_shares} shares @ ${existing_position.average_entry_price:.2f} avg")
                else:
                    # Complete sale - remove position
                    # TODO: Implement position deletion logic
                    logger.info(f"Position closed completely by selling {trade_result['quantity']} shares")
        
        # CALCULATE EQUITY CORRECTLY
        # Get current cash from previous equity record
        equity_history = db_ops.get_equity_history()
        previous_cash = equity_history[-1].cash if equity_history else current_equity
        
        # Calculate cash change based on trade
        if side == 'buy':
            new_cash = previous_cash - (trade_result['quantity'] * trade_result['price'])
        else:  # sell
            new_cash = previous_cash + (trade_result['quantity'] * trade_result['price'])
        
        # Calculate total portfolio value
        total_position_value = 0
        for pos in db_ops.get_positions():
            total_position_value += pos.quantity * pos.current_price
        
        total_portfolio_value = new_cash + total_position_value
        
        equity_data = {
            'equity': total_portfolio_value,
            'cash': new_cash,
            'total_value': total_portfolio_value,
            'timestamp': trade_result['timestamp']
        }
        update_equity(equity_data)
        
        logger.info(f"Portfolio update: Cash=${new_cash:.2f}, Positions=${total_position_value:.2f}, Total=${total_portfolio_value:.2f}")

        logger.info("Trading cycle completed successfully")
        monitor.record_success()
    except Exception as e:
        error_msg = f"Error in trading cycle: {e}"
        logger.error(error_msg, exc_info=True)
        monitor.record_failure(error_msg)

def main():
    # Setup application
    setup_application()
    
    parser = argparse.ArgumentParser(description="AI Trading Bot Main Loop")
    parser.add_argument('--symbols', type=str, default=os.environ.get("TRADING_SYMBOLS", "AAPL,MSFT,JNJ,UNH,V"), help="Comma-separated ticker symbols to trade (default: top 5 Dow Jones)")
    parser.add_argument('--loop', action='store_true', help="Run in infinite loop mode (default: single run)")
    parser.add_argument('--max-loops', type=int, default=None, help="Maximum number of loop iterations (for testing)")
    parser.add_argument('--interval', type=int, default=int(os.environ.get("TRADING_INTERVAL", "300")), help="Interval between trading cycles in seconds (default: 300)")
    args = parser.parse_args()

    if args.loop:
        start_time = datetime.now(timezone.utc)
        cycle_count = 0
        
        # Start health check server in background thread
        health_port = int(os.environ.get("PORT", "8080"))
        health_thread = threading.Thread(target=start_health_server, args=(health_port,), daemon=True)
        health_thread.start()
        
        # Update bot status
        bot_status['status'] = 'running'
        
        logger.info("=" * 60)
        logger.info("🚀 TRADING BOT BACKGROUND WORKER STARTING")
        logger.info(f"\ud83d\udcca Symbols: {args.symbols}")
        print(f"\ud83d\udcca Trading Symbols: {args.symbols}")
        symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
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
                bot_status['cycles_completed'] = cycle_count
                
                logger.info("=" * 40)
                logger.info(f"📈 TRADING CYCLE #{cycle_count} STARTING")
                logger.info(f"📊 Symbol: {args.symbol}")
                logger.info(f"🕐 Time: {current_time.strftime('%H:%M:%S UTC')}")
                logger.info("=" * 40)
                
                print(f"📈 Running trading cycle #{cycle_count} for {args.symbol}")
                
                for symbol in symbols:
                    logger.info(f"\ud83d\udcc8 Running trading cycle #{cycle_count} for {symbol}")
                    print(f"\ud83d\udcc8 Running trading cycle #{cycle_count} for {symbol}")
                    run_trading_cycle(symbol)
                
                bot_status['last_cycle_time'] = current_time
                logger.info(f"✅ Trading cycle #{cycle_count} completed")
                print(f"✅ Trading cycle #{cycle_count} completed")
                
                # Log next cycle info
                next_cycle_time = current_time.timestamp() + args.interval
                next_cycle_datetime = datetime.fromtimestamp(next_cycle_time, timezone.utc)
                next_cycle_str = next_cycle_datetime.strftime('%H:%M:%S UTC')
                bot_status['next_cycle_time'] = next_cycle_datetime
                
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
        symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
        for symbol in symbols:
            run_trading_cycle(symbol)

if __name__ == "__main__":
    main() 