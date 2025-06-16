import time
import logging
import argparse
import sys
from backend.app.services.fetcher import fetch_ohlcv
from bot.strategy.signals import generate_signals
from bot.risk.risk import calculate_position_size
from backend.app.services.broker.paper import execute_trade
from backend.app.db.supabase import update_trades, update_positions, update_equity
from backend.app.core.config import load_config
from backend.app.utils.helpers import log_function_call, exponential_backoff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@log_function_call
@exponential_backoff(max_retries=3, base_delay=1)
def run_trading_cycle(symbol: str = "AAPL"):
    try:
        # Load configuration
        cfg = load_config()
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

        # Get current equity and open positions from DB or config (placeholder logic)
        current_equity = cfg.get('STARTING_EQUITY', 100000)
        open_positions = 0  # TODO: fetch from DB if available

        # Calculate position size based on risk
        position_size = calculate_position_size(signals, current_equity, open_positions)
        if not position_size:
            logger.info("No position size calculated")
            return

        # Determine trade side from signals (placeholder logic)
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
    parser = argparse.ArgumentParser(description="AI Trading Bot Main Loop")
    parser.add_argument('--symbol', type=str, default="AAPL", help="Ticker symbol to trade")
    parser.add_argument('--loop', action='store_true', help="Run in infinite loop mode (default: single run)")
    parser.add_argument('--max-loops', type=int, default=None, help="Maximum number of loop iterations (for testing)")
    args = parser.parse_args()

    if args.loop:
        count = 0
        while True:
            run_trading_cycle(args.symbol)
            count += 1
            if args.max_loops is not None and count >= args.max_loops:
                break
            time.sleep(300)  # Sleep for 5 minutes
    else:
        run_trading_cycle(args.symbol)

if __name__ == "__main__":
    main() 