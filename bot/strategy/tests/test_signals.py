import unittest
import pandas as pd
import numpy as np
from bot.strategy.signals import generate_signals

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

    def test_generate_signals_valid(self):
        data = pd.DataFrame({'close': list(range(100, 150))})
        result = generate_signals(data)
        self.assertIsInstance(result, dict)
        self.assertIn('signal', result)
        self.assertIn('data', result)

    def test_generate_signals_empty(self):
        data = pd.DataFrame()
        result = generate_signals(data)
        self.assertIsNone(result)

    def test_generate_signals_missing_close(self):
        data = pd.DataFrame({'open': [1, 2, 3]})
        result = generate_signals(data)
        self.assertIsNone(result)

    def test_generate_signals_short_data(self):
        data = pd.DataFrame({'close': [100, 101]})
        result = generate_signals(data)
        self.assertIsInstance(result, dict)
        self.assertIn('signal', result)
        self.assertIn('data', result)

if __name__ == "__main__":
    unittest.main() 