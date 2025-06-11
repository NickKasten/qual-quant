import time
import logging
from data.fetcher import fetch_ohlcv
from strategy.signals import generate_signals
from strategy.risk import calculate_position_size
from broker.paper import execute_trade
from db.supabase import update_trades, update_positions, update_equity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    while True:
        try:
            # Fetch OHLCV data
            data = fetch_ohlcv()
            if not data:
                logger.error("Failed to fetch OHLCV data")
                time.sleep(300)  # Sleep for 5 minutes
                continue

            # Generate trading signals
            signals = generate_signals(data)
            if not signals:
                logger.info("No signals generated")
                time.sleep(300)
                continue

            # Calculate position size based on risk
            position_size = calculate_position_size(signals)
            if not position_size:
                logger.info("No position size calculated")
                time.sleep(300)
                continue

            # Execute simulated trade
            trade_result = execute_trade(position_size)
            if not trade_result:
                logger.error("Failed to execute trade")
                time.sleep(300)
                continue

            # Update database with trade, positions, and equity
            update_trades(trade_result)
            update_positions(trade_result)
            update_equity(trade_result)

            logger.info("Trading cycle completed successfully")
            time.sleep(300)  # Sleep for 5 minutes

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main() 