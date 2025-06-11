from typing import Dict, Optional

def calculate_position_size(signals: Dict) -> Optional[Dict]:
    """
    Calculate position size based on 2% equity per trade, 5% stop-loss, and max 3 open positions.
    """
    if not signals or 'signal' not in signals:
        return None

    signal = signals['signal']
    if signal == 0:
        return None

    # Example: Assume equity is 10000
    equity = 10000
    risk_per_trade = equity * 0.02  # 2% equity per trade
    stop_loss_pct = 0.05  # 5% stop-loss

    # Calculate position size
    position_size = risk_per_trade / stop_loss_pct

    # Check if max positions (3) is exceeded
    # This is a placeholder; you would need to check current open positions
    max_positions = 3
    current_positions = 0  # Placeholder

    if current_positions >= max_positions:
        return None

    return {'position_size': position_size, 'signal': signal} 