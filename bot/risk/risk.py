import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def calculate_position_size(signals: Dict, current_equity: float, open_positions: int, current_price: float) -> Optional[Dict]:
    """
    Calculate position size based on 2% equity per trade, 5% stop-loss, and max 3 open positions.
    Returns a dictionary containing the position size and metadata.
    
    Args:
        signals: Signal data with direction and strength
        current_equity: Total portfolio equity available
        open_positions: Number of currently open positions
        current_price: Current stock price for position sizing
    """
    logger.info(f"Calculating position size with signals: {signals}, equity: {current_equity}, open positions: {open_positions}, price: {current_price}")
    
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

    # Calculate position size using CORRECT formula
    risk_per_trade = current_equity * 0.02  # 2% equity per trade ($2,000 on $100K)
    stop_loss_pct = 0.05  # 5% stop-loss
    
    # Maximum investment amount (not shares!)
    max_investment = risk_per_trade / stop_loss_pct  # $2,000 / 0.05 = $40,000 max
    
    # Calculate shares based on current stock price
    position_size = int(max_investment / current_price)  # $40,000 / $105 = ~381 shares
    
    # Calculate actual investment amount
    actual_investment = position_size * current_price
    
    logger.info(f"Risk calculation: ${risk_per_trade:.2f} risk / {stop_loss_pct*100}% stop = ${max_investment:.2f} max investment")
    logger.info(f"Position size: {position_size} shares @ ${current_price:.2f} = ${actual_investment:.2f} total")
    
    return {
        'position_size': position_size,
        'risk_per_trade': risk_per_trade,
        'stop_loss_pct': stop_loss_pct,
        'max_investment': max_investment,
        'actual_investment': actual_investment,
        'current_price': current_price
    } 