import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def calculate_position_size(signals: Dict, current_equity: float, open_positions: int) -> Optional[int]:
    """
    Calculate position size based on 2% equity per trade, 5% stop-loss, and max 3 open positions.
    Returns the number of shares to trade as an integer.
    """
    logger.info(f"Calculating position size with signals: {signals}, equity: {current_equity}, open positions: {open_positions}")
    
    if not signals or 'signal' not in signals:
        logger.warning("No signals or missing signal key")
        return None

    signal = signals['signal']
    if signal == 0:
        logger.info("No trading signal (signal = 0)")
        return None

    # Check if max positions (3) is exceeded
    max_positions = 3
    if open_positions >= max_positions:
        logger.info(f"Max positions ({max_positions}) exceeded")
        return None

    # Calculate position size
    risk_per_trade = current_equity * 0.02  # 2% equity per trade
    stop_loss_pct = 0.05  # 5% stop-loss
    position_size = int(risk_per_trade / stop_loss_pct)  # Convert to integer
    
    logger.info(f"Calculated position size: {position_size}")
    return position_size 