from typing import Dict, Optional

def calculate_position_size(signals: Dict, current_equity: float, open_positions: int) -> Optional[Dict]:
    """
    Calculate position size based on 2% equity per trade, 5% stop-loss, and max 3 open positions.
    """
    if not signals or 'signal' not in signals:
        return None

    signal = signals['signal']
    if signal == 0:
        return None

    # Check if max positions (3) is exceeded
    max_positions = 3
    if open_positions >= max_positions:
        return None

    # Calculate position size
    risk_per_trade = current_equity * 0.02  # 2% equity per trade
    stop_loss_pct = 0.05  # 5% stop-loss
    position_size = risk_per_trade / stop_loss_pct

    return {'position_size': position_size, 'signal': signal} 