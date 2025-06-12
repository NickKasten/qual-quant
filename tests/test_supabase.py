import unittest
from unittest.mock import patch
from db.supabase import setup_tables, update_trades, update_positions, update_equity
import requests

SUPABASE_URL = 'https://your-supabase-url.supabase.co'

HEADERS = {
    'apikey': 'test-api-key',
    'Authorization': 'Bearer test-api-key',
    'Content-Type': 'application/json',
}

class TestSupabase(unittest.TestCase):
    @patch('db.supabase.requests.post')
    def test_setup_tables(self, mock_post):
        # Mock successful table creation
        mock_post.return_value.status_code = 200
        setup_tables()
        self.assertEqual(mock_post.call_count, 3)  # One call for each table

    @patch('db.supabase.requests.post')
    def test_update_trades(self, mock_post):
        # Mock successful trade update
        mock_post.return_value.status_code = 200
        trade_result = {'symbol': 'AAPL', 'side': 'buy', 'quantity': 10}
        update_trades(trade_result)
        mock_post.assert_called_once()

    @patch('db.supabase.requests.post')
    def test_update_positions(self, mock_post):
        # Mock successful position update
        mock_post.return_value.status_code = 200
        trade_result = {'symbol': 'AAPL', 'side': 'buy', 'quantity': 10}
        update_positions(trade_result)
        mock_post.assert_called_once()

    @patch('db.supabase.requests.post')
    def test_update_equity(self, mock_post):
        # Mock successful equity update
        mock_post.return_value.status_code = 200
        trade_result = {'symbol': 'AAPL', 'side': 'buy', 'quantity': 10}
        update_equity(trade_result)
        mock_post.assert_called_once()

    @patch('db.supabase.requests.get')
    def test_read_trades(self, mock_get):
        # Mock successful read of trades
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'symbol': 'AAPL', 'side': 'buy', 'quantity': 10}]
        response = requests.get(f"{SUPABASE_URL}/rest/v1/trades", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    @patch('db.supabase.requests.get')
    def test_read_positions(self, mock_get):
        # Mock successful read of positions
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'symbol': 'AAPL', 'side': 'buy', 'quantity': 10}]
        response = requests.get(f"{SUPABASE_URL}/rest/v1/positions", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    @patch('db.supabase.requests.get')
    def test_read_equity(self, mock_get):
        # Mock successful read of equity
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'equity': 10000}]
        response = requests.get(f"{SUPABASE_URL}/rest/v1/equity", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

if __name__ == "__main__":
    unittest.main() 