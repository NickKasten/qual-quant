import unittest
from unittest.mock import patch, MagicMock
import os
import requests
from datetime import datetime, UTC
import importlib
import sys
from broker import paper
from broker.paper import (
    execute_trade,
    validate_order_inputs,
    validate_api_credentials,
    get_order_status,
    OrderValidationError,
    get_trade_log,
    clear_trade_log
)
from requests import Timeout

class TestPaperTrading(unittest.TestCase):
    def setUp(self):
        # Set up test environment variables
        os.environ['ALPACA_API_KEY'] = 'test_api_key'
        os.environ['ALPACA_SECRET_KEY'] = 'test_secret_key'
        importlib.reload(paper)
        self.test_symbol = "AAPL"
        self.test_side = "buy"
        self.test_position_size = 10

    def tearDown(self):
        # Clean up environment variables
        os.environ.pop('ALPACA_API_KEY', None)
        os.environ.pop('ALPACA_SECRET_KEY', None)
        importlib.reload(paper)

    def test_validate_api_credentials(self):
        # Test valid credentials
        is_valid, msg = paper.validate_api_credentials()
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

        # Test missing credentials
        os.environ.pop('ALPACA_API_KEY')
        os.environ.pop('ALPACA_SECRET_KEY')
        importlib.reload(paper)
        is_valid, msg = paper.validate_api_credentials()
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Missing API credentials")

    def test_validate_order_inputs(self):
        # Test valid inputs
        is_valid, msg = validate_order_inputs(self.test_position_size, self.test_symbol, self.test_side)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

        # Test invalid position size
        is_valid, msg = validate_order_inputs(0, self.test_symbol, self.test_side)
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Position size must be a positive integer")

        # Test invalid symbol
        is_valid, msg = validate_order_inputs(self.test_position_size, "", self.test_side)
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Invalid symbol")

        # Test invalid side
        is_valid, msg = validate_order_inputs(self.test_position_size, self.test_symbol, "invalid")
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Invalid order side. Must be 'buy' or 'sell'")

    @patch('broker.paper.requests.post')
    def test_execute_trade_success(self, mock_post):
        # Mock a successful Alpaca API response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'status': 'filled',
            'id': 'order123',
            'filled_avg_price': '101.23',
            'created_at': '2024-03-20T10:00:00Z'
        }
        result = execute_trade(self.test_position_size, symbol=self.test_symbol, side=self.test_side, simulate=False)
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], self.test_symbol)
        self.assertEqual(result['side'], self.test_side)
        self.assertEqual(result['quantity'], self.test_position_size)

    # @patch('broker.paper.requests.post')
    # def test_execute_trade_api_error(self, mock_post):
    #     mock_post.return_value.status_code = 400
    #     mock_post.return_value.text = "Invalid order"
    #     with self.assertRaises(OrderValidationError) as cm:
    #         execute_trade(self.test_position_size, symbol=self.test_symbol, side=self.test_side, simulate=False)
    #     self.assertIn("Failed to place order: Invalid order", str(cm.exception))

    # @patch('broker.paper.requests.post')
    # def test_execute_trade_timeout(self, mock_post):
    #     mock_post.side_effect = Timeout()
    #     with self.assertRaises(OrderValidationError) as cm:
    #         execute_trade(self.test_position_size, symbol=self.test_symbol, side=self.test_side, simulate=False)
    #     self.assertIn("Request timed out while placing order", str(cm.exception))

    @patch('broker.paper.requests.get')
    def test_get_order_status_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'status': 'filled',
            'id': 'order123',
            'filled_avg_price': '101.23'
        }
        result = get_order_status('order123')
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'filled')

    @patch('broker.paper.requests.get')
    def test_get_order_status_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        result = get_order_status('nonexistent')
        self.assertIsNone(result)

    def test_simulated_trade_execution_and_tracking(self):
        clear_trade_log()
        trade = execute_trade(self.test_position_size, symbol=self.test_symbol, side=self.test_side, simulate=True)
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], self.test_symbol)
        self.assertEqual(trade['side'], self.test_side)
        self.assertEqual(trade['quantity'], self.test_position_size)
        self.assertTrue(trade['simulated'])
        # Trade log should contain this trade
        log = get_trade_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]['order_id'], trade['order_id'])
        # Clear log and check
        clear_trade_log()
        self.assertEqual(get_trade_log(), [])

if __name__ == "__main__":
    unittest.main() 