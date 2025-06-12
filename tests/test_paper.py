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

class TestPaperTrading(unittest.TestCase):
    def setUp(self):
        # Set up test environment variables
        os.environ['ALPACA_API_KEY'] = 'test_api_key'
        os.environ['ALPACA_SECRET_KEY'] = 'test_secret_key'
        importlib.reload(paper)

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
        position_size = {'position_size': 10}
        is_valid, msg = validate_order_inputs(position_size, 'AAPL', 'buy')
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

        # Test invalid position size
        is_valid, msg = validate_order_inputs({}, 'AAPL', 'buy')
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Invalid position size data")

        # Test invalid symbol
        is_valid, msg = validate_order_inputs(position_size, '', 'buy')
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Invalid symbol")

        # Test invalid side
        is_valid, msg = validate_order_inputs(position_size, 'AAPL', 'invalid')
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Invalid order side. Must be 'buy' or 'sell'")

        # Test invalid quantity
        is_valid, msg = validate_order_inputs({'position_size': -1}, 'AAPL', 'buy')
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Quantity must be greater than 0")

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
        position_size = {'position_size': 10}
        result = execute_trade(position_size, symbol='AAPL', side='buy', simulate=False)
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'filled')
        self.assertEqual(result['order_id'], 'order123')
        self.assertEqual(result['filled_avg_price'], '101.23')
        self.assertEqual(result['timestamp'], '2024-03-20T10:00:00Z')

    @patch('broker.paper.requests.post')
    def test_execute_trade_api_error(self, mock_post):
        # Mock API error response
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = 'Bad Request'
        position_size = {'position_size': 10}
        with self.assertRaises(paper.OrderValidationError):
            execute_trade(position_size, symbol='AAPL', side='buy', simulate=False)

    @patch('broker.paper.requests.post')
    def test_execute_trade_timeout(self, mock_post):
        # Mock timeout error
        mock_post.side_effect = requests.Timeout()
        position_size = {'position_size': 10}
        with self.assertRaises(paper.OrderValidationError):
            execute_trade(position_size, symbol='AAPL', side='buy', simulate=False)

    @patch('broker.paper.requests.post')
    def test_execute_trade_validation_error(self, mock_post):
        # Test invalid position size
        with self.assertRaises(paper.OrderValidationError):
            execute_trade({}, symbol='AAPL', side='buy')

        # Test invalid symbol
        with self.assertRaises(paper.OrderValidationError):
            execute_trade({'position_size': 10}, symbol='', side='buy')

        # Test invalid side
        with self.assertRaises(paper.OrderValidationError):
            execute_trade({'position_size': 10}, symbol='AAPL', side='invalid')

    @patch('broker.paper.requests.get')
    def test_get_order_status_success(self, mock_get):
        # Mock successful order status response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': 'order123',
            'status': 'filled',
            'filled_avg_price': '101.23'
        }
        result = get_order_status('order123')
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'filled')
        self.assertEqual(result['filled_avg_price'], '101.23')

    @patch('broker.paper.requests.get')
    def test_get_order_status_failure(self, mock_get):
        # Mock failed order status response
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = 'Order not found'
        result = get_order_status('invalid_order')
        self.assertIsNone(result)

    def test_simulated_trade_execution_and_tracking(self):
        clear_trade_log()
        position_size = {'position_size': 5}
        trade = execute_trade(position_size, symbol='AAPL', side='buy', simulate=True)
        self.assertTrue(trade['simulated'])
        self.assertEqual(trade['status'], 'filled')
        self.assertEqual(trade['symbol'], 'AAPL')
        self.assertEqual(trade['side'], 'buy')
        self.assertEqual(trade['quantity'], 5)
        self.assertIn('filled_avg_price', trade)
        # Trade log should contain this trade
        log = get_trade_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]['order_id'], trade['order_id'])
        # Clear log and check
        clear_trade_log()
        self.assertEqual(get_trade_log(), [])

if __name__ == "__main__":
    unittest.main() 