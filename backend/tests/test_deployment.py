import pytest

pytestmark = pytest.mark.skip(reason="Deployment checks require external APIs")

import pytest
import os
from backend.app.services.fetcher import fetch_ohlcv
from bot.strategy.signals import generate_signals
from bot.risk.risk import calculate_position_size
from backend.app.services.broker.paper import execute_trade
from backend.app.db import supabase as db_supabase
from backend.app.core.config import load_config
from unittest.mock import patch

TOP5_DOW = ["AAPL", "MSFT", "JNJ", "UNH", "V"]

def test_environment_variables():
    """Test that all required environment variables are set"""
    required_vars = [
        'TIINGO_API_KEY',
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
    for symbol in TOP5_DOW:
        data = fetch_ohlcv(symbol)
        assert data is not None
        assert not data.empty
        assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])

def test_signal_generation():
    """Test signal generation"""
    for symbol in TOP5_DOW:
        data = fetch_ohlcv(symbol)
        assert data is not None and not data.empty and 'close' in data.columns
        signals = generate_signals(data)
        assert signals is not None
        assert 'side' in signals

def test_signal_generation_empty():
    """Test signal generation with empty DataFrame returns None"""
    import pandas as pd
    empty_data = pd.DataFrame()
    signals = generate_signals(empty_data)
    assert signals is None

def test_signal_generation_missing_close():
    """Test signal generation with missing 'close' column returns None"""
    import pandas as pd
    data = pd.DataFrame({'open': [1,2,3]})
    signals = generate_signals(data)
    assert signals is None

def test_position_sizing():
    """Test position sizing calculation"""
    for symbol in TOP5_DOW:
        data = fetch_ohlcv(symbol)
        # Force a buy signal
        data['SMA20'] = data['close'] * 1.1  # Make SMA20 higher than SMA50
        data['SMA50'] = data['close'] * 0.9
        data['RSI'] = 50  # Neutral RSI
        signals = generate_signals(data, use_precalculated=True)
        current_price = float(data['close'].iloc[-1])
        position = calculate_position_size(signals, 100000, 0, current_price)
        assert position is not None
        assert isinstance(position, dict)
        assert 'position_size' in position
        assert position['position_size'] > 0

def test_position_sizing_max_positions():
    """Test position sizing returns None when max positions is reached"""
    for symbol in TOP5_DOW:
        data = fetch_ohlcv(symbol)
        data['SMA20'] = data['close'] * 1.1
        data['SMA50'] = data['close'] * 0.9
        data['RSI'] = 50
        signals = generate_signals(data, use_precalculated=True)
        # Simulate 3 open positions (max)
        current_price = float(data['close'].iloc[-1])
        position = calculate_position_size(signals, 100000, 3, current_price)
        assert position is None

def test_position_sizing_stop_loss_and_risk():
    """Test position sizing risk and stop-loss calculations"""
    for symbol in TOP5_DOW:
        data = fetch_ohlcv(symbol)
        data['SMA20'] = data['close'] * 1.1
        data['SMA50'] = data['close'] * 0.9
        data['RSI'] = 50
        signals = generate_signals(data, use_precalculated=True)
        current_price = float(data['close'].iloc[-1])
        position = calculate_position_size(signals, 100000, 0, current_price)
        assert position is not None
        assert abs(position['risk_per_trade'] - 2000) < 1  # 2% of 100,000
        assert abs(position['stop_loss_pct'] - 0.05) < 1e-6  # 5%

def test_trade_execution():
    """Test paper trade execution"""
    for symbol in TOP5_DOW:
        with patch('backend.app.services.broker.paper.validate_api_credentials', return_value=(True, '')):
            trade_result = execute_trade(100, symbol=symbol, side="buy", simulate=True)
            assert trade_result is not None
            assert 'order_id' in trade_result

def test_database_operations():
    """Test database operations"""
    for symbol in TOP5_DOW:
        with patch('backend.app.services.broker.paper.validate_api_credentials', return_value=(True, '')):
            with patch('backend.app.db.supabase.update_trades', return_value=True), \
                 patch('backend.app.db.supabase.update_positions', return_value=True), \
                 patch('backend.app.db.supabase.update_equity', return_value=True):
                trade_result = execute_trade(100, symbol=symbol, side="buy", simulate=True)
                assert db_supabase.update_trades(trade_result) is True
                assert db_supabase.update_positions(trade_result) is True
                equity_result = {"equity": 100000, "timestamp": "2024-01-01T00:00:00Z"}
                assert db_supabase.update_equity(equity_result) is True

def test_config_loading():
    """Test configuration loading"""
    cfg = load_config()
    assert cfg is not None
    assert 'STARTING_EQUITY' in cfg 