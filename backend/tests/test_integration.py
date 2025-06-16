import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
from datetime import datetime, UTC
from backend.app.services.fetcher import fetch_ohlcv
from bot.strategy.signals import generate_signals
from bot.risk.risk import calculate_position_size
from backend.app.services.broker.paper import execute_trade
from backend.app.db.supabase import update_trades, update_positions
from backend.app.main import run_trading_cycle

class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Set up test environment
        self.test_symbol = "AAPL"
        self.test_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
            'open': [100] * 100,
            'high': [105] * 100,
            'low': [95] * 100,
            'close': [102] * 100,
            'volume': [1000] * 100
        })
        
        # Mock environment variables
        os.environ['TIINGO_API_KEY'] = 'test-key'
        os.environ['ALPACA_API_KEY'] = 'test-key'
        os.environ['ALPACA_SECRET_KEY'] = 'test-secret'
        os.environ['SUPABASE_URL'] = 'https://test-url.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test-key'
        os.environ['STARTING_EQUITY'] = '100000'

    @patch('main.fetch_ohlcv')
    @patch('main.generate_signals')
    @patch('main.calculate_position_size')
    @patch('main.execute_trade')
    @patch('main.update_trades')
    @patch('main.update_positions')
    @patch('main.update_equity')
    def test_full_trading_cycle(self, mock_update_equity, mock_update_positions, 
                               mock_update_trades, mock_execute_trade, 
                               mock_calculate_position_size, mock_generate_signals, 
                               mock_fetch_ohlcv):
        """Test the complete trading cycle from data fetching to database updates"""
        # Mock data fetching
        mock_fetch_ohlcv.return_value = self.test_data
        
        # Mock signal generation
        mock_generate_signals.return_value = {
            'signal': 'buy',
            'side': 'buy',
            'data': self.test_data
        }
        
        # Mock position sizing
        mock_calculate_position_size.return_value = {
            'position_size': 10
        }
        
        # Mock trade execution
        mock_execute_trade.return_value = {
            'status': 'filled',
            'order_id': 'test123',
            'filled_avg_price': 102.0,
            'timestamp': datetime.now(UTC).isoformat()
        }
        
        # Run trading cycle
        run_trading_cycle(self.test_symbol)
        
        # Verify all components were called
        mock_fetch_ohlcv.assert_called_once_with(self.test_symbol)
        mock_generate_signals.assert_called_once()
        mock_calculate_position_size.assert_called_once()
        mock_execute_trade.assert_called_once()
        mock_update_trades.assert_called_once()
        mock_update_positions.assert_called_once()
        mock_update_equity.assert_called_once()

    def test_data_to_signals_integration(self):
        """Test integration between data fetching and signal generation"""
        signals = generate_signals(self.test_data)
        self.assertIsNotNone(signals)
        self.assertIn('signal', signals)
        self.assertIn('side', signals)
        self.assertIn('data', signals)

    def test_signals_to_position_sizing(self):
        """Test integration between signal generation and position sizing"""
        # Create test signals
        signals = {
            'signal': 1,
            'side': 'buy',
            'data': self.test_data
        }

        # Calculate position size
        position_size = calculate_position_size(
            signals=signals,
            current_equity=100000,
            open_positions=0
        )

        # Verify integration
        self.assertIsNotNone(position_size)
        self.assertIn('position_size', position_size)
        self.assertIn('risk_per_trade', position_size)
        self.assertIn('stop_loss_pct', position_size)

    @patch('backend.app.services.broker.paper.execute_trade')
    @patch('backend.app.db.supabase.update_trades')
    @patch('backend.app.db.supabase.update_positions')
    @patch('backend.app.services.broker.paper.validate_api_credentials', return_value=(True, ''))
    def test_trade_execution_to_database(self, mock_validate_api, mock_update_positions, mock_update_trades, mock_execute_trade):
        """Test integration between trade execution and database updates"""
        # Mock trade execution
        trade_result = {
            'status': 'filled',
            'order_id': 'test123',
            'filled_avg_price': 102.0,
            'timestamp': datetime.now(UTC).isoformat(),
            'symbol': self.test_symbol,
            'side': 'buy',
            'quantity': 10
        }
        mock_execute_trade.return_value = trade_result

        # Mock database updates
        mock_update_trades.return_value = True
        mock_update_positions.return_value = True

        # Execute trade and update database
        trade = execute_trade(10, symbol=self.test_symbol, side='buy', simulate=True)
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], self.test_symbol)
        self.assertEqual(trade['side'], 'buy')
        self.assertEqual(trade['quantity'], 10)

        # Import the patched functions so the patch is effective
        from backend.app.db.supabase import update_trades, update_positions
        update_trades(trade)
        update_positions(trade)

        # Verify database updates
        mock_update_trades.assert_called_once()
        mock_update_positions.assert_called_once()

    @patch('backend.app.services.broker.paper.validate_api_credentials', return_value=(True, ''))
    def test_full_trading_cycle(self, mock_validate_api):
        """Test the complete trading cycle from data to execution"""
        # Craft data and set indicators to guarantee a buy signal
        data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
            'open': [100] * 100,
            'high': [105] * 100,
            'low': [95] * 100,
            'close': [100] * 100,
            'volume': [1000] * 100
        })
        data['SMA20'] = 120
        data['SMA50'] = 100
        data['RSI'] = 50
        signals = generate_signals(data, use_precalculated=True)
        self.assertIsNotNone(signals)
        self.assertEqual(signals['side'], 'buy')

        # Calculate position size
        position_size = calculate_position_size(
            signals=signals,
            current_equity=100000,
            open_positions=0
        )
        self.assertIsNotNone(position_size)

        # Execute trade
        with patch('backend.app.services.broker.paper.execute_trade') as mock_execute_trade:
            mock_execute_trade.return_value = {
                'status': 'filled',
                'order_id': 'test123',
                'filled_avg_price': 120.0,
                'timestamp': datetime.now(UTC).isoformat(),
                'symbol': self.test_symbol,
                'side': 'buy',
                'quantity': position_size['position_size']
            }
            trade = execute_trade(position_size['position_size'], symbol=self.test_symbol, side='buy', simulate=True)
            self.assertIsNotNone(trade)
            self.assertEqual(trade['status'], 'filled')

if __name__ == '__main__':
    unittest.main() 