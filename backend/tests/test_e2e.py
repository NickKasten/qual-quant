
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from backend.app.main import run_trading_cycle


@pytest.fixture
def mock_config():
    return {
        'STARTING_EQUITY': 100000.0,
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
        'signal': 1,
        'strength': 0.8,
        'data': pd.DataFrame({'close': [105]})
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


def _mock_db_ops(empty_positions=True):
    db_ops = MagicMock()
    db_ops.get_recent_trades.return_value = []
    db_ops.get_positions.return_value = [] if empty_positions else [MagicMock(quantity=10)]
    equity_record = MagicMock()
    equity_record.cash = 50000.0
    db_ops.get_equity_history.return_value = [equity_record]
    return db_ops


class TestEndToEnd:
    @patch('backend.app.main.DatabaseOperations')
    @patch('backend.app.main.update_equity')
    @patch('backend.app.main.update_positions')
    @patch('backend.app.main.update_trades')
    @patch('backend.app.main.execute_trade')
    @patch('backend.app.main.calculate_position_size')
    @patch('backend.app.main.generate_signals')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.load_config')
    def test_complete_trading_cycle(
        self,
        mock_load_config,
        mock_fetch_ohlcv,
        mock_generate_signals,
        mock_calculate_position_size,
        mock_execute_trade,
        mock_update_trades,
        mock_update_positions,
        mock_update_equity,
        mock_db_ops_factory,
        mock_config,
        mock_ohlcv_data,
        mock_signals,
        mock_trade_result
    ):
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = mock_ohlcv_data
        mock_generate_signals.return_value = mock_signals
        mock_calculate_position_size.return_value = {'position_size': 10}
        mock_execute_trade.return_value = mock_trade_result
        mock_db_ops_factory.return_value = _mock_db_ops()

        run_trading_cycle('AAPL')

        mock_fetch_ohlcv.assert_called_once_with('AAPL')
        mock_generate_signals.assert_called_once()
        mock_calculate_position_size.assert_called_once()
        mock_execute_trade.assert_called_once()
        assert mock_update_trades.called
        assert mock_update_positions.called
        assert mock_update_equity.called

    @patch('backend.app.main.DatabaseOperations')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.load_config')
    def test_trading_cycle_with_empty_data(
        self,
        mock_load_config,
        mock_fetch_ohlcv,
        mock_db_ops_factory,
        mock_config
    ):
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = None
        mock_db_ops_factory.return_value = _mock_db_ops()

        run_trading_cycle('AAPL')

        mock_fetch_ohlcv.assert_called_once_with('AAPL')

    @patch('backend.app.main.DatabaseOperations')
    @patch('backend.app.main.generate_signals')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.load_config')
    def test_trading_cycle_with_no_signals(
        self,
        mock_load_config,
        mock_fetch_ohlcv,
        mock_generate_signals,
        mock_db_ops_factory,
        mock_config,
        mock_ohlcv_data
    ):
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = mock_ohlcv_data
        mock_generate_signals.return_value = None
        mock_db_ops_factory.return_value = _mock_db_ops()

        run_trading_cycle('AAPL')

        mock_fetch_ohlcv.assert_called_once_with('AAPL')
        mock_generate_signals.assert_called_once_with(mock_ohlcv_data, existing_position=0)

    @patch('backend.app.main.DatabaseOperations')
    @patch('backend.app.main.calculate_position_size')
    @patch('backend.app.main.generate_signals')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.load_config')
    def test_trading_cycle_with_no_position_size(
        self,
        mock_load_config,
        mock_fetch_ohlcv,
        mock_generate_signals,
        mock_calculate_position_size,
        mock_db_ops_factory,
        mock_config,
        mock_ohlcv_data,
        mock_signals
    ):
        mock_load_config.return_value = mock_config
        mock_fetch_ohlcv.return_value = mock_ohlcv_data
        mock_generate_signals.return_value = mock_signals
        mock_calculate_position_size.return_value = None
        mock_db_ops_factory.return_value = _mock_db_ops()

        run_trading_cycle('AAPL')

        mock_fetch_ohlcv.assert_called_once_with('AAPL')
        mock_generate_signals.assert_called_once()
        mock_calculate_position_size.assert_called_once()
