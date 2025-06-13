import unittest
from unittest.mock import patch
import logging
from utils import log_function_call, exponential_backoff

class TestUtils(unittest.TestCase):
    @patch('utils.logger')
    def test_log_function_call(self, mock_logger):
        @log_function_call
        def test_func(x, y):
            return x + y
        result = test_func(1, 2)
        self.assertEqual(result, 3)
        self.assertTrue(mock_logger.info.called)
        self.assertFalse(mock_logger.error.called)

    @patch('utils.logger')
    def test_log_function_call_error(self, mock_logger):
        @log_function_call
        def test_func():
            raise ValueError("Test error")
        with self.assertRaises(ValueError):
            test_func()
        self.assertTrue(mock_logger.error.called)

    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep):
        @exponential_backoff(max_retries=3, base_delay=1)
        def test_func():
            return "success"
        result = test_func()
        self.assertEqual(result, "success")
        self.assertEqual(mock_sleep.call_count, 0)

    @patch('time.sleep')
    def test_exponential_backoff_retry(self, mock_sleep):
        @exponential_backoff(max_retries=3, base_delay=1)
        def test_func():
            raise ValueError("Test error")
        with self.assertRaises(ValueError):
            test_func()
        self.assertEqual(mock_sleep.call_count, 3)

if __name__ == "__main__":
    unittest.main() 