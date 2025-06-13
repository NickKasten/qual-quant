import unittest
from unittest.mock import patch
from main import run_trading_cycle

class TestMain(unittest.TestCase):
    @patch('main.load_config')
    @patch('main.fetch_ohlcv')
    @patch('main.generate_signals')
    @patch('main.calculate_position_size')
    @patch('main.execute_trade')
    @patch('main.update_trades')
    @patch('main.update_positions')
    @patch('main.update_equity')
    def test_run_trading_cycle_success(self, mock_update_equity, mock_update_positions, mock_update_trades, mock_execute_trade, mock_calculate_position_size, mock_generate_signals, mock_fetch_ohlcv, mock_load_config):
        mock_load_config.return_value = {'TIIINGO_API_KEY': 'test-key', 'SUPABASE_URL': 'test-url', 'SUPABASE_KEY': 'test-key'}
        mock_fetch_ohlcv.return_value = {'data': 'test_data'}
        mock_generate_signals.return_value = {'signal': 'buy'}
        mock_calculate_position_size.return_value = {'size': 10}
        mock_execute_trade.return_value = {'trade': 'success'}
        run_trading_cycle()
        mock_update_trades.assert_called_once()
        mock_update_positions.assert_called_once()
        mock_update_equity.assert_called_once()

    @patch('main.load_config')
    @patch('main.fetch_ohlcv')
    @patch('main.update_trades')
    @patch('main.update_positions')
    @patch('main.update_equity')
    def test_run_trading_cycle_fetch_failure(self, mock_update_equity, mock_update_positions, mock_update_trades, mock_fetch_ohlcv, mock_load_config):
        mock_load_config.return_value = {'TIIINGO_API_KEY': 'test-key', 'SUPABASE_URL': 'test-url', 'SUPABASE_KEY': 'test-key'}
        mock_fetch_ohlcv.return_value = None
        run_trading_cycle()
        # Verify no updates were made
        self.assertFalse(mock_update_trades.called)
        self.assertFalse(mock_update_positions.called)
        self.assertFalse(mock_update_equity.called)

if __name__ == "__main__":
    unittest.main() 