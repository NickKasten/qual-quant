import unittest
import pandas as pd
from strategy.backtest import run_backtest

class TestBacktest(unittest.TestCase):
    def setUp(self):
        # Create sample data for testing
        self.data = pd.DataFrame({
            'Open': [100] * 100,
            'High': [105] * 100,
            'Low': [95] * 100,
            'Close': [102] * 100,
            'Volume': [1000] * 100
        })

    def test_backtest(self):
        # Run backtest
        stats = run_backtest(self.data)
        self.assertIsNotNone(stats)
        self.assertIn('Return [%]', stats)

if __name__ == "__main__":
    unittest.main() 