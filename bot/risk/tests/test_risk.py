import unittest
from bot.risk.risk import calculate_position_size

class TestRisk(unittest.TestCase):
    def test_no_open_positions(self):
        # Test with no open positions
        signals = {'signal': 1}
        current_equity = 10000
        open_positions = 0
        result = calculate_position_size(signals, current_equity, open_positions)
        self.assertIsNotNone(result)
        self.assertIn('position_size', result)

    def test_max_open_positions(self):
        # Test with max open positions
        signals = {'signal': 1}
        current_equity = 10000
        open_positions = 3
        result = calculate_position_size(signals, current_equity, open_positions)
        self.assertIsNone(result)

    def test_equity_changes(self):
        # Test with different equity values
        signals = {'signal': 1}
        current_equity = 20000
        open_positions = 0
        result = calculate_position_size(signals, current_equity, open_positions)
        self.assertIsNotNone(result)
        self.assertIn('position_size', result)

if __name__ == "__main__":
    unittest.main() 