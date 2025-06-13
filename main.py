import time
import logging
from data.fetcher import fetch_ohlcv
from strategy.signals import generate_signals
from strategy.risk import calculate_position_size
from broker.paper import execute_trade
from db.supabase import update_trades, update_positions, update_equity
from config import load_config
from utils import log_function_call, exponential_backoff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@log_function_call
@exponential_backoff(max_retries=3, base_delay=1)
def run_trading_cycle():
    try:
        # Load configuration
        cfg = load_config()
        logger.info("Configuration loaded successfully")

        # Fetch OHLCV data
        data = fetch_ohlcv()
        if not data:
            logger.error("Failed to fetch OHLCV data")
            return

        # Generate trading signals
        signals = generate_signals(data)
        if not signals:
            logger.info("No signals generated")
            return

        # Calculate position size based on risk
        position_size = calculate_position_size(signals)
        if not position_size:
            logger.info("No position size calculated")
            return

        # Execute simulated trade
        trade_result = execute_trade(position_size)
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
    while True:
        run_trading_cycle()
        time.sleep(300)  # Sleep for 5 minutes

if __name__ == "__main__":
    main() 