import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_signal_strength(data: pd.DataFrame, signal: int) -> float:
    """
    Calculate signal strength based on technical indicators.
    Returns a value between 0.0 and 1.0.
    """
    latest_row = data.iloc[-1]
    
    # Base strength on RSI distance from neutral (50)
    rsi = latest_row['RSI']
    if pd.isna(rsi):
        return 0.5  # Neutral if RSI unavailable
    
    if signal == 1:  # Buy signal
        # Stronger buy when RSI is oversold (closer to 30)
        rsi_strength = max(0, (50 - rsi) / 20)  # 0-1 scale, stronger as RSI approaches 30
        base_strength = 0.5 + (rsi_strength * 0.4)  # 0.5-0.9 range
    elif signal == -1:  # Sell signal
        # Stronger sell when RSI is overbought (closer to 70)
        rsi_strength = max(0, (rsi - 50) / 20)  # 0-1 scale, stronger as RSI approaches 70
        base_strength = 0.5 + (rsi_strength * 0.4)  # 0.5-0.9 range
    else:  # Hold signal
        # Strength based on how close RSI is to neutral (50)
        rsi_neutrality = 1 - abs(rsi - 50) / 50  # Closer to 50 = higher strength
        base_strength = 0.3 + (rsi_neutrality * 0.4)  # 0.3-0.7 range
    
    # Add SMA crossover strength if both SMA values are available
    sma20 = latest_row['SMA20']
    sma50 = latest_row['SMA50']
    
    if not pd.isna(sma20) and not pd.isna(sma50):
        # Calculate percentage difference between SMAs
        sma_diff = abs(sma20 - sma50) / sma50
        sma_strength = min(sma_diff * 10, 0.1)  # Cap at 0.1 boost
        
        if signal != 0:  # For buy/sell signals, add SMA strength
            base_strength = min(1.0, base_strength + sma_strength)
    
    return round(base_strength, 4)

def validate_data_sufficiency(data: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate if we have sufficient data for indicators.
    Returns dict with validation results.
    """
    return {
        'has_sma20_data': len(data) >= 20,
        'has_sma50_data': len(data) >= 50,
        'has_rsi_data': len(data) >= 14,
        'total_days': len(data)
    }

def generate_signals(data: pd.DataFrame, use_precalculated: bool = False) -> Optional[Dict]:
    """
    Generate trading signals based on 20/50 SMA crossover and RSI filter (70/30).
    Returns a dictionary with signal (-1, 0, 1), side ('buy', 'sell', 'hold'), strength, and the processed data.
    
    Args:
        data: DataFrame with OHLCV data
        use_precalculated: If True, use existing SMA20, SMA50, and RSI columns
    """
    if data.empty or 'close' not in data.columns:
        logger.error("Invalid data: empty or missing 'close' column")
        return None

    # Validate data sufficiency
    validation = validate_data_sufficiency(data)
    logger.info(f"Data validation: {validation}")
    
    # Use fallback strategy if insufficient data for SMA50
    use_fallback = not validation['has_sma50_data']
    if use_fallback:
        logger.warning(f"Insufficient data for SMA50 ({validation['total_days']} days < 50 required). Using fallback strategy.")

    if not use_precalculated:
        # Calculate indicators
        if use_fallback:
            # Fallback: Use 10/20 SMA instead of 20/50
            data['SMA10'] = data['close'].rolling(window=10).mean()
            data['SMA20'] = data['close'].rolling(window=20).mean()
            data['SMA50'] = np.nan  # Mark as unavailable
        else:
            # Standard: 20/50 SMA
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
    
    if use_fallback and 'SMA10' in data.columns:
        # Fallback strategy: 10/20 SMA crossover
        data.loc[(data['SMA10'] > data['SMA20']) & (data['RSI'] < 70), 'signal'] = 1  # Buy
        data.loc[(data['SMA10'] < data['SMA20']) & (data['RSI'] > 30), 'signal'] = -1  # Sell
        logger.info("Using fallback strategy: 10/20 SMA crossover")
    else:
        # Standard strategy: 20/50 SMA crossover
        data.loc[(data['SMA20'] > data['SMA50']) & (data['RSI'] < 70), 'signal'] = 1  # Buy
        data.loc[(data['SMA20'] < data['SMA50']) & (data['RSI'] > 30), 'signal'] = -1  # Sell

    # Get the latest signal
    latest_signal = data['signal'].iloc[-1]
    if pd.isna(latest_signal):
        latest_signal = 0
        
    latest_signal = int(latest_signal)
    
    if latest_signal == 1:
        side = 'buy'
    elif latest_signal == -1:
        side = 'sell'
    else:
        side = 'hold'
    
    # Calculate signal strength
    strength = calculate_signal_strength(data, latest_signal)
    
    logger.info(f"Generated signal: {latest_signal} ({side}) with strength {strength}")
    
    return {
        'signal': latest_signal,
        'side': side,
        'strength': strength,
        'data': data,
        'used_fallback': use_fallback,
        'validation': validation
    } 