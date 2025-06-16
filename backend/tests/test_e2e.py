import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import run_trading_cycle
from backend.app.services.fetcher import fetch_ohlcv
from bot.strategy.signals import generate_signals
from backend.app.services.broker.paper import execute_trade
from backend.app.db.supabase import update_trades, update_positions, update_equity
from backend.app.main import load_config

@pytest.fixture
def mock_config():
    return {
        'STARTING_EQUITY': 100000,
        'API_KEY': 'test_key',
        'API_SECRET': 'test_secret',
        'DB_URL': 'test_url',
        'DB_KEY': 'test_key'
    }

@pytest.fixture
def mock_ohlcv_data():
    return pd.DataFrame({
        'open': [100, 101, 102, 103, 104],
        'high': [105, 106, 107, 108, 109],
        'low': [95, 96, 97, 98, 99],
        'close': [101, 102, 103, 104, 105],
        'volume': [1000, 1100, 1200, 1300, 1400]
    }, index=pd.date_range(start='2024-01-01', periods=5))

@pytest.fixture
def mock_signals():
    return {
        'side': 'buy',
        'strength': 0.8,
        'timestamp': pd.Timestamp('2024-01-01')
    }

@pytest.fixture
def mock_trade_result():
    return {
        'symbol': 'AAPL',
        'side': 'buy',
        'quantity': 10,
        'price': 100.0,
        'timestamp': pd.Timestamp('2024-01-01'),
        'status': 'filled'
    }

class TestEndToEnd:
    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.generate_signals')
    @patch('backend.app.main.calculate_position_size')
    @patch('backend.app.main.execute_trade')
    @patch('backend.app.main.update_trades')
    @patch('backend.app.main.update_positions')
    @patch('backend.app.main.update_equity')
    def test_complete_trading_cycle(
        self,
        mock_update_equity,
        mock_update_positions,
        mock_update_trades,
        mock_execute_trade,
        mock_calculate_position_size,
        mock_generate_signals,
        mock_fetch_ohlcv,
        mock_load_config,
        mock_config,
        mock_ohlcv_data,
        mock_signals,
        mock_trade_result
    ):
        # Setup mocks
        mock_config = {
            'API_KEY': 'test_key',
            'API_SECRET': 'test_secret',
            'DB_KEY': 'test_key',
            'DB_URL': 'test_url',
            'STARTING_EQUITY': 100000.0  # Ensure this is a float
        }
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = mock_ohlcv_data
        mock_generate_signals.return_value = mock_signals
        mock_calculate_position_size.return_value = 10
        mock_execute_trade.return_value = mock_trade_result
        mock_update_trades.return_value = True
        mock_update_positions.return_value = True
        mock_update_equity.return_value = True

        # Run the trading cycle
        run_trading_cycle('AAPL')

        # Verify all components were called with correct parameters
        mock_load_config.assert_called_once()
        mock_fetch_ohlcv.assert_called_once_with('AAPL')
        mock_generate_signals.assert_called_once_with(mock_ohlcv_data)
        mock_calculate_position_size.assert_called_once_with(mock_signals, 100000.0, 0)
        mock_execute_trade.assert_called_once_with(10, symbol='AAPL', side='buy', simulate=True)
        mock_update_trades.assert_called_once_with(mock_trade_result)
        mock_update_positions.assert_called_once_with(mock_trade_result)
        mock_update_equity.assert_called_once_with(mock_trade_result)

    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    def test_trading_cycle_with_empty_data(
        self,
        mock_fetch_ohlcv,
        mock_load_config,
        mock_config
    ):
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = None

        # Run the trading cycle
        run_trading_cycle('AAPL')

        # Verify fetch_ohlcv was called but no other components
        mock_fetch_ohlcv.assert_called_once_with('AAPL')

    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.generate_signals')
    def test_trading_cycle_with_no_signals(
        self,
        mock_generate_signals,
        mock_fetch_ohlcv,
        mock_load_config,
        mock_config,
        mock_ohlcv_data
    ):
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = mock_ohlcv_data
        mock_generate_signals.return_value = None

        # Run the trading cycle
        run_trading_cycle('AAPL')

        # Verify components were called but no trade execution
        mock_fetch_ohlcv.assert_called_once_with('AAPL')
        mock_generate_signals.assert_called_once_with(mock_ohlcv_data)

    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.generate_signals')
    @patch('backend.app.main.calculate_position_size')
    def test_trading_cycle_with_no_position_size(
        self,
        mock_calculate_position_size,
        mock_generate_signals,
        mock_fetch_ohlcv,
        mock_load_config,
        mock_config,
        mock_ohlcv_data,
        mock_signals
    ):
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = mock_ohlcv_data
        mock_generate_signals.return_value = mock_signals
        mock_calculate_position_size.return_value = None

        # Run the trading cycle
        run_trading_cycle('AAPL')

        # Verify components were called but no trade execution
        mock_fetch_ohlcv.assert_called_once_with('AAPL')
        mock_generate_signals.assert_called_once_with(mock_ohlcv_data)
        mock_calculate_position_size.assert_called_once_with(
            mock_signals,
            mock_config['STARTING_EQUITY'],
            0
        ) 