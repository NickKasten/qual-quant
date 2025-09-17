
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from backend.app.main import run_trading_cycle, main

TOP5_DOW = ["AAPL", "MSFT", "JNJ", "UNH", "V"]

class TestMain(unittest.TestCase):
    @patch('backend.app.main.DatabaseOperations')
    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.generate_signals')
    @patch('backend.app.main.calculate_position_size')
    @patch('backend.app.main.execute_trade')
    @patch('backend.app.main.update_trades')
    @patch('backend.app.main.update_positions')
    @patch('backend.app.main.update_equity')
    @patch('backend.app.main.update_signals')
    def test_run_trading_cycle_success(self, mock_update_signals, mock_update_equity, mock_update_positions, mock_update_trades, mock_execute_trade, mock_calculate_position_size, mock_generate_signals, mock_fetch_ohlcv, mock_load_config, mock_db_ops):
        mock_load_config.return_value = {'TIINGO_API_KEY': 'test-key', 'SUPABASE_URL': 'test-url', 'SUPABASE_KEY': 'test-key', 'STARTING_EQUITY': 100000}
        mock_fetch_ohlcv.return_value = pd.DataFrame({'close': [100.0]})
        mock_generate_signals.return_value = {'signal': 1, 'side': 'buy', 'strength': 0.8}
        mock_calculate_position_size.return_value = {'position_size': 10}
        mock_execute_trade.return_value = {
            'symbol': 'AAPL',
            'side': 'buy',
            'quantity': 10,
            'price': 100.0,
            'timestamp': pd.Timestamp('2024-01-01'),
            'strategy': 'test'
        }
        mock_db_ops.return_value.get_recent_trades.return_value = []
        mock_db_ops.return_value.get_positions.return_value = []
        equity_record = MagicMock()
        equity_record.cash = 50000.0
        mock_db_ops.return_value.get_equity_history.return_value = [equity_record]

        run_trading_cycle(symbol='AAPL')

        mock_update_trades.assert_called_once()
        mock_update_positions.assert_called_once()
        mock_update_equity.assert_called_once()

    @patch('backend.app.main.DatabaseOperations')
    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.update_trades')
    @patch('backend.app.main.update_positions')
    @patch('backend.app.main.update_equity')
    def test_run_trading_cycle_fetch_failure(self, mock_update_equity, mock_update_positions, mock_update_trades, mock_fetch_ohlcv, mock_load_config, mock_db_ops):
        mock_load_config.return_value = {'TIINGO_API_KEY': 'test-key', 'SUPABASE_URL': 'test-url', 'SUPABASE_KEY': 'test-key'}
        mock_fetch_ohlcv.return_value = None
        mock_db_ops.return_value.get_recent_trades.return_value = []

        run_trading_cycle(symbol='AAPL')

        self.assertFalse(mock_update_trades.called)
        self.assertFalse(mock_update_positions.called)
        self.assertFalse(mock_update_equity.called)

    @patch('backend.app.main.run_background_bot')
    @patch('backend.app.main.argparse.ArgumentParser.parse_args')
    def test_main_single_run(self, mock_parse_args, mock_run_background_bot):
        args = MagicMock()
        args.mode = 'bot'
        args.symbols = 'AAPL'
        args.interval = 3600
        args.max_loops = None
        args.host = '0.0.0.0'
        args.port = None
        args.loop = False
        mock_parse_args.return_value = args

        main()

        mock_run_background_bot.assert_called_once()

    @patch('backend.app.main.run_background_bot')
    @patch('backend.app.main.argparse.ArgumentParser.parse_args')
    def test_main_loop_mode(self, mock_parse_args, mock_run_background_bot):
        args = MagicMock()
        args.mode = 'bot'
        args.symbols = 'AAPL'
        args.interval = 3600
        args.max_loops = 1
        args.host = '0.0.0.0'
        args.port = None
        args.loop = True
        mock_parse_args.return_value = args

        main()

        mock_run_background_bot.assert_called_once_with('AAPL', 3600, 1, 8080)

if __name__ == "__main__":
    unittest.main()
