import pandas as pd
import numpy as np
from typing import Dict, Optional

def generate_signals(data: pd.DataFrame, use_precalculated: bool = False) -> Optional[Dict]:
    """
    Generate trading signals based on 20/50 SMA crossover and RSI filter (70/30).
    Returns a dictionary with signal (-1, 0, 1) and side ('buy', 'sell', 'hold').
    
    Args:
        data: DataFrame with OHLCV data
        use_precalculated: If True, use existing SMA20, SMA50, and RSI columns
    """
    if data.empty or 'close' not in data.columns:
        return None

    if not use_precalculated:
        # Calculate SMA
        data['SMA20'] = data['close'].rolling(window=20).mean()
        data['SMA50'] = data['close'].rolling(window=50).mean()

        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

    # Generate signals
    data['signal'] = 0
    data.loc[(data['SMA20'] > data['SMA50']) & (data['RSI'] < 70), 'signal'] = 1  # Buy
    data.loc[(data['SMA20'] < data['SMA50']) & (data['RSI'] > 30), 'signal'] = -1  # Sell

    # Return the latest signal
    latest_signal = data['signal'].iloc[-1]
    if latest_signal == 1:
        side = 'buy'
    elif latest_signal == -1:
        side = 'sell'
    else:
        side = 'hold'
    
    return {'signal': latest_signal, 'side': side} 