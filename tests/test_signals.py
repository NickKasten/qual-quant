import unittest
import pandas as pd
import numpy as np
from strategy.signals import generate_signals

class TestStrategySignals(unittest.TestCase):
    def setUp(self):
        # Create sample data for testing
        self.data = {
            'date': pd.date_range(start='2023-01-01', periods=100, freq='D'),
            'close': np.random.rand(100) * 100
        }
        self.df = pd.DataFrame(self.data)

    def test_sma_crossover(self):
        # Test SMA crossover logic
        signals = generate_signals(self.df)
        self.assertIsNotNone(signals)
        self.assertIn('signal', signals)

    def test_rsi_filter(self):
        # Test RSI filter logic
        signals = generate_signals(self.df)
        self.assertIsNotNone(signals)
        self.assertIn('signal', signals)

if __name__ == "__main__":
    unittest.main() 