import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC
from backend.app.db.supabase import (
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
            'order_id': 'test123',
            'symbol': 'AAPL',
            'side': 'buy',
            'quantity': 10,
            'filled_avg_price': 102.0,
            'timestamp': datetime.now(UTC).isoformat(),
            'status': 'filled'
        }

        self.valid_position = {
            'symbol': 'AAPL',
            'quantity': 10,
            'filled_avg_price': 102.0,
            'current_price': 102.0,
            'market_value': 1020.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'last_updated': datetime.now(UTC).isoformat()
        }

        self.valid_equity = {
            'timestamp': datetime.now(UTC).isoformat(),
            'equity': 100000.0,
            'cash': 90000.0,
            'buying_power': 90000.0
        }

    def test_validate_trade_data(self):
        """Test trade data validation"""
        self.assertTrue(validate_trade_data(self.valid_trade))
        invalid_trade = self.valid_trade.copy()
        invalid_trade.pop('order_id')
        self.assertFalse(validate_trade_data(invalid_trade))

    def test_validate_position_data(self):
        """Test position data validation"""
        self.assertTrue(validate_position_data(self.valid_position))
        invalid_position = self.valid_position.copy()
        invalid_position.pop('symbol')
        self.assertFalse(validate_position_data(invalid_position))

    def test_validate_equity_data(self):
        """Test equity data validation"""
        self.assertTrue(validate_equity_data(self.valid_equity))
        invalid_equity = self.valid_equity.copy()
        invalid_equity.pop('equity')
        self.assertFalse(validate_equity_data(invalid_equity))

    @patch('backend.app.db.supabase.requests.post')
    def test_setup_tables(self, mock_post):
        """Test table setup"""
        mock_post.return_value.status_code = 200
        setup_tables()
        self.assertEqual(mock_post.call_count, 3)  # One call for each table

    @patch('backend.app.db.supabase.requests.post')
    def test_update_trades_success(self, mock_post):
        """Test successful trade update"""
        mock_post.return_value.status_code = 200
        result = update_trades(self.valid_trade)
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('backend.app.db.supabase.requests.post')
    def test_update_trades_invalid_data(self, mock_post):
        """Test trade update with invalid data"""
        invalid_trade = self.valid_trade.copy()
        invalid_trade.pop('order_id')
        result = update_trades(invalid_trade)
        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch('backend.app.db.supabase.requests.post')
    def test_update_positions_success(self, mock_post):
        """Test successful position update"""
        mock_post.return_value.status_code = 200
        result = update_positions(self.valid_position)
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('backend.app.db.supabase.requests.post')
    def test_update_positions_invalid_data(self, mock_post):
        """Test position update with invalid data"""
        invalid_position = self.valid_position.copy()
        invalid_position.pop('symbol')
        result = update_positions(invalid_position)
        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch('backend.app.db.supabase.requests.post')
    def test_update_equity_success(self, mock_post):
        """Test successful equity update"""
        mock_post.return_value.status_code = 200
        result = update_equity(self.valid_equity)
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('backend.app.db.supabase.requests.post')
    def test_update_equity_invalid_data(self, mock_post):
        """Test equity update with invalid data"""
        invalid_equity = self.valid_equity.copy()
        invalid_equity.pop('equity')
        result = update_equity(invalid_equity)
        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch('backend.app.db.supabase.requests.get')
    def test_read_trades(self, mock_get):
        """Test reading trades from database"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [self.valid_trade]
        result = read_trades()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('backend.app.db.supabase.requests.get')
    def test_read_positions(self, mock_get):
        """Test reading positions from database"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [self.valid_position]
        result = read_positions()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('backend.app.db.supabase.requests.get')
    def test_read_equity_history(self, mock_get):
        """Test reading equity history from database"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [self.valid_equity]
        result = read_equity_history()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('backend.app.db.supabase.requests.get')
    def test_read_operations_error_handling(self, mock_get):
        """Test error handling in read operations"""
        mock_get.return_value.status_code = 500
        result = read_trades()
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main() 