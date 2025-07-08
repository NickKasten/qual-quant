import unittest
from unittest.mock import patch, MagicMock
from backend.app.main import run_trading_cycle, main

TOP5_DOW = ["AAPL", "MSFT", "JNJ", "UNH", "V"]

class TestMain(unittest.TestCase):
    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.generate_signals')
    @patch('backend.app.main.calculate_position_size')
    @patch('backend.app.main.execute_trade')
    @patch('backend.app.main.update_trades')
    @patch('backend.app.main.update_positions')
    @patch('backend.app.main.update_equity')
    def test_run_trading_cycle_success(self, mock_update_equity, mock_update_positions, mock_update_trades, mock_execute_trade, mock_calculate_position_size, mock_generate_signals, mock_fetch_ohlcv, mock_load_config):
        mock_load_config.return_value = {'TIINGO_API_KEY': 'test-key', 'SUPABASE_URL': 'test-url', 'SUPABASE_KEY': 'test-key', 'STARTING_EQUITY': 100000}
        mock_fetch_ohlcv.return_value = MagicMock(empty=False)
        mock_generate_signals.return_value = {'signal': 'buy', 'side': 'buy'}
        mock_calculate_position_size.return_value = {'size': 10}
        mock_execute_trade.return_value = {'trade': 'success'}
        for symbol in TOP5_DOW:
            run_trading_cycle(symbol=symbol)
        mock_update_trades.assert_called_once()
        mock_update_positions.assert_called_once()
        mock_update_equity.assert_called_once()

    @patch('backend.app.main.load_config')
    @patch('backend.app.main.fetch_ohlcv')
    @patch('backend.app.main.update_trades')
    @patch('backend.app.main.update_positions')
    @patch('backend.app.main.update_equity')
    def test_run_trading_cycle_fetch_failure(self, mock_update_equity, mock_update_positions, mock_update_trades, mock_fetch_ohlcv, mock_load_config):
        mock_load_config.return_value = {'TIINGO_API_KEY': 'test-key', 'SUPABASE_URL': 'test-url', 'SUPABASE_KEY': 'test-key'}
        mock_fetch_ohlcv.return_value = None
        for symbol in TOP5_DOW:
            run_trading_cycle(symbol=symbol)
        # Verify no updates were made
        self.assertFalse(mock_update_trades.called)
        self.assertFalse(mock_update_positions.called)
        self.assertFalse(mock_update_equity.called)

    @patch('backend.app.main.run_trading_cycle')
    @patch('backend.app.main.argparse.ArgumentParser.parse_args')
    def test_main_single_run(self, mock_parse_args, mock_run_trading_cycle):
        mock_parse_args.return_value = MagicMock(symbol="AAPL", loop=False)
        main()
        mock_run_trading_cycle.assert_called_once_with("AAPL")

    @patch('backend.app.main.run_trading_cycle')
    @patch('backend.app.main.argparse.ArgumentParser.parse_args')
    @patch('backend.app.main.time.sleep')
    def test_main_loop_mode(self, mock_sleep, mock_parse_args, mock_run_trading_cycle):
        mock_parse_args.return_value = MagicMock(symbol="AAPL", loop=True, max_loops=1)
        main()
        mock_run_trading_cycle.assert_called_with("AAPL")
        mock_sleep.assert_not_called()

if __name__ == "__main__":
    unittest.main() 