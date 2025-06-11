import pandas as pd
import numpy as np
from typing import Dict, Optional

def generate_signals(data: Dict) -> Optional[Dict]:
    """
    Generate trading signals based on 20/50 SMA crossover and RSI filter (70/30).
    """
    if not data:
        return None

    # Convert data to DataFrame
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    # Calculate SMA
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['SMA50'] = df['close'].rolling(window=50).mean()

    # Calculate RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Generate signals
    df['signal'] = 0
    df.loc[(df['SMA20'] > df['SMA50']) & (df['RSI'] < 70), 'signal'] = 1  # Buy
    df.loc[(df['SMA20'] < df['SMA50']) & (df['RSI'] > 30), 'signal'] = -1  # Sell

    # Return the latest signal
    latest_signal = df['signal'].iloc[-1]
    return {'signal': latest_signal, 'data': df.to_dict()} 