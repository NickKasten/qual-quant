import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC
from db.supabase import (
    setup_tables,
    update_trades,
    update_positions,
    update_equity,
    read_trades,
    read_positions,
    read_equity_history,
    validate_trade_data,
    validate_position_data,
    validate_equity_data
)

SUPABASE_URL = 'https://your-supabase-url.supabase.co'

HEADERS = {
    'apikey': 'test-api-key',
    'Authorization': 'Bearer test-api-key',
    'Content-Type': 'application/json',
}

class TestSupabase(unittest.TestCase):
    def setUp(self):
        self.valid_trade = {
            'symbol': 'AAPL',
            'side': 'buy',
            'quantity': 10,
            'status': 'filled',
            'order_id': '123',
            'filled_avg_price': 150.0,
            'timestamp': datetime.now(UTC).isoformat()
        }
        
        self.valid_position = {
            'symbol': 'AAPL',
            'quantity': 10,
            'avg_entry_price': 150.0,
            'current_price': 155.0,
            'market_value': 1550.0
        }
        
        self.valid_equity = {
            'equity': 10000.0,
            'timestamp': datetime.now(UTC).isoformat()
        }

    def test_validate_trade_data(self):
        """Test trade data validation"""
        self.assertTrue(validate_trade_data(self.valid_trade))
        invalid_trade = self.valid_trade.copy()
        del invalid_trade['symbol']
        self.assertFalse(validate_trade_data(invalid_trade))

    def test_validate_position_data(self):
        """Test position data validation"""
        self.assertTrue(validate_position_data(self.valid_position))
        invalid_position = self.valid_position.copy()
        del invalid_position['quantity']
        self.assertFalse(validate_position_data(invalid_position))

    def test_validate_equity_data(self):
        """Test equity data validation"""
        self.assertTrue(validate_equity_data(self.valid_equity))
        invalid_equity = self.valid_equity.copy()
        del invalid_equity['equity']
        self.assertFalse(validate_equity_data(invalid_equity))

    @patch('db.supabase.requests.post')
    def test_setup_tables(self, mock_post):
        """Test table setup"""
        mock_post.return_value.status_code = 200
        setup_tables()
        self.assertEqual(mock_post.call_count, 3)  # One call for each table

    @patch('db.supabase.requests.post')
    def test_update_trades_success(self, mock_post):
        """Test successful trade update"""
        mock_post.return_value.status_code = 200
        update_trades(self.valid_trade)
        mock_post.assert_called_once()

    @patch('db.supabase.requests.post')
    def test_update_trades_invalid_data(self, mock_post):
        """Test trade update with invalid data"""
        invalid_trade = self.valid_trade.copy()
        del invalid_trade['symbol']
        update_trades(invalid_trade)
        mock_post.assert_not_called()

    @patch('db.supabase.requests.post')
    def test_update_positions_success(self, mock_post):
        """Test successful position update"""
        mock_post.return_value.status_code = 200
        update_positions(self.valid_position)
        mock_post.assert_called_once()

    @patch('db.supabase.requests.post')
    def test_update_positions_invalid_data(self, mock_post):
        """Test position update with invalid data"""
        invalid_position = self.valid_position.copy()
        del invalid_position['quantity']
        update_positions(invalid_position)
        mock_post.assert_not_called()

    @patch('db.supabase.requests.post')
    def test_update_equity_success(self, mock_post):
        """Test successful equity update"""
        mock_post.return_value.status_code = 200
        update_equity(self.valid_equity)
        mock_post.assert_called_once()

    @patch('db.supabase.requests.post')
    def test_update_equity_invalid_data(self, mock_post):
        """Test equity update with invalid data"""
        invalid_equity = self.valid_equity.copy()
        del invalid_equity['equity']
        update_equity(invalid_equity)
        mock_post.assert_not_called()

    @patch('db.supabase.requests.get')
    def test_read_trades(self, mock_get):
        """Test reading trades"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [self.valid_trade]
        mock_get.return_value = mock_response

        # Test reading all trades
        trades = read_trades()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['symbol'], 'AAPL')

        # Test reading trades for specific symbol
        trades = read_trades(symbol='AAPL')
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['symbol'], 'AAPL')

    @patch('db.supabase.requests.get')
    def test_read_positions(self, mock_get):
        """Test reading positions"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [self.valid_position]
        mock_get.return_value = mock_response

        # Test reading all positions
        positions = read_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], 'AAPL')

        # Test reading positions for specific symbol
        positions = read_positions(symbol='AAPL')
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], 'AAPL')

    @patch('db.supabase.requests.get')
    def test_read_equity_history(self, mock_get):
        """Test reading equity history"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [self.valid_equity]
        mock_get.return_value = mock_response

        equity_history = read_equity_history(days=30)
        self.assertEqual(len(equity_history), 1)
        self.assertEqual(equity_history[0]['equity'], 10000.0)

    @patch('db.supabase.requests.get')
    def test_read_operations_error_handling(self, mock_get):
        """Test error handling in read operations"""
        mock_get.return_value.status_code = 500

        # Test error handling for trades
        trades = read_trades()
        self.assertEqual(trades, [])

        # Test error handling for positions
        positions = read_positions()
        self.assertEqual(positions, [])

        # Test error handling for equity history
        equity_history = read_equity_history()
        self.assertEqual(equity_history, [])

if __name__ == "__main__":
    unittest.main() 