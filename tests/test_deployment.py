import pytest
import os
from data.fetcher import fetch_ohlcv
from strategy.signals import generate_signals
from strategy.risk import calculate_position_size
from broker.paper import execute_trade
from db.supabase import update_trades, update_positions, update_equity
from config import load_config

def test_environment_variables():
    """Test that all required environment variables are set"""
    required_vars = [
        'TIIINGO_API_KEY',
        'ALPHA_VANTAGE_API_KEY',
        'ALPACA_API_KEY',
        'ALPACA_SECRET_KEY',
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    for var in required_vars:
        assert os.getenv(var) is not None, f"Environment variable {var} is not set"

def test_data_fetching():
    """Test data fetching functionality"""
    data = fetch_ohlcv("AAPL")
    assert data is not None
    assert not data.empty
    assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])

def test_signal_generation():
    """Test signal generation"""
    data = fetch_ohlcv("AAPL")
    signals = generate_signals(data)
    assert signals is not None
    assert 'side' in signals

def test_position_sizing():
    """Test position sizing calculation"""
    data = fetch_ohlcv("AAPL")
    # Force a buy signal
    data['SMA20'] = data['close'] * 1.1  # Make SMA20 higher than SMA50
    data['SMA50'] = data['close'] * 0.9
    data['RSI'] = 50  # Neutral RSI
    signals = generate_signals(data, use_precalculated=True)
    position_size = calculate_position_size(signals, 100000, 0)
    assert position_size is not None
    assert position_size > 0

def test_trade_execution():
    """Test paper trade execution"""
    trade_result = execute_trade(100, symbol="AAPL", side="buy", simulate=True)
    assert trade_result is not None
    assert 'order_id' in trade_result

def test_database_operations():
    """Test database operations"""
    trade_result = execute_trade(100, symbol="AAPL", side="buy", simulate=True)
    assert update_trades(trade_result) is True
    assert update_positions(trade_result) is True
    equity_result = {"equity": 100000, "timestamp": "2024-01-01T00:00:00Z"}
    assert update_equity(equity_result) is True

def test_config_loading():
    """Test configuration loading"""
    cfg = load_config()
    assert cfg is not None
    assert 'STARTING_EQUITY' in cfg 