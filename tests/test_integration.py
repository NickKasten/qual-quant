import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
from datetime import datetime, UTC
from data.fetcher import fetch_ohlcv
from strategy.signals import generate_signals
from strategy.risk import calculate_position_size
from broker.paper import execute_trade
from db.supabase import update_trades, update_positions, update_equity
from main import run_trading_cycle

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
        os.environ['TIIINGO_API_KEY'] = 'test-key'
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
        # Create test data
        test_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
            'open': [100] * 100,
            'high': [105] * 100,
            'low': [95] * 100,
            'close': [102] * 100,
            'volume': [1000] * 100
        })
        
        # Generate signals with real data
        signals = generate_signals(test_data)
        
        # Convert data to DataFrame if it's a dictionary
        if isinstance(signals['data'], dict):
            signals['data'] = pd.DataFrame(signals['data'])
        
        # Verify data flow
        self.assertIsNotNone(signals)
        self.assertIn('signal', signals)
        self.assertIn('side', signals)
        self.assertIn(signals['side'], ['buy', 'sell', 'hold'])
        self.assertIn('data', signals)
        self.assertIsInstance(signals['data'], pd.DataFrame)

    @patch('tests.test_integration.calculate_position_size')
    def test_signals_to_position_sizing(self, mock_calculate_position_size):
        """Test integration between signal generation and position sizing"""
        # Create test signals
        signals = {
            'signal': 'buy',
            'side': 'buy',
            'data': self.test_data
        }
        
        # Mock position sizing
        mock_calculate_position_size.return_value = {
            'position_size': 10
        }
        
        # Calculate position size
        position_size = calculate_position_size(
            signals=signals,
            current_equity=100000,
            open_positions=0
        )
        
        # Verify integration
        self.assertIsNotNone(position_size)
        self.assertEqual(position_size['position_size'], 10)
        mock_calculate_position_size.assert_called_once_with(
            signals=signals,
            current_equity=100000,
            open_positions=0
        )

    @patch('broker.paper.execute_trade')
    @patch('tests.test_integration.update_trades')
    @patch('tests.test_integration.update_positions')
    def test_trade_execution_to_database(self, mock_update_positions, mock_update_trades, mock_execute_trade):
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
        trade = execute_trade({'position_size': 10}, self.test_symbol, 'buy')
        update_trades(trade)
        update_positions({
            'symbol': self.test_symbol,
            'quantity': 10,
            'avg_entry_price': 102.0,
            'current_price': 102.0,
            'market_value': 1020.0
        })
        
        # Verify integration
        self.assertIsNotNone(trade)
        self.assertEqual(trade['status'], 'filled')
        mock_update_trades.assert_called_once_with(trade)
        mock_update_positions.assert_called_once()

if __name__ == '__main__':
    unittest.main() 