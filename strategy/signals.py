import pandas as pd
import numpy as np
from typing import Dict, Optional

def generate_signals(data: pd.DataFrame) -> Optional[Dict]:
    """
    Generate trading signals based on 20/50 SMA crossover and RSI filter (70/30).
    """
    if data.empty or 'close' not in data.columns:
        return None

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
    return {'signal': latest_signal, 'side': side, 'data': data.to_dict()} 