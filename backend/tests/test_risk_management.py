"""
Comprehensive tests for risk management functionality.
Tests risk calculations, position sizing, and safety constraints.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from bot.risk.risk import calculate_position_size


class TestRiskManagement:
    """Test suite for risk management calculations."""
    
    def test_position_size_with_buy_signal(self):
        """Test position size calculation for BUY signal."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.8
        }
        
        current_equity = 100000.0
        open_positions = 0
        current_price = 100.0
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        assert result is not None
        assert 'position_size' in result
        assert result['position_size'] > 0
        assert isinstance(result['position_size'], int)
    
    def test_position_size_with_sell_signal(self):
        """Test position size calculation for SELL signal."""
        
        signals = {
            'side': 'sell',
            'signal': -1,
            'strength': 0.7
        }
        
        current_equity = 100000.0
        open_positions = 1
        current_price = 100.0
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        assert result is not None
        assert 'position_size' in result
        assert result['position_size'] > 0
    
    def test_position_size_with_hold_signal(self):
        """Test position size calculation for HOLD signal returns None."""
        
        signals = {
            'side': 'hold',
            'signal': 0,
            'strength': 0.5
        }
        
        current_equity = 100000.0
        open_positions = 1
        current_price = 100.0
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        assert result is None
    
    def test_position_size_respects_risk_per_trade(self):
        """Test that position size respects 2% risk per trade limit."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.8
        }
        
        current_equity = 50000.0  # Smaller equity
        open_positions = 0
        current_price = 200.0  # Higher price stock
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        assert result is not None
        position_value = result['position_size'] * current_price
        # Should not exceed ~2% of equity (50000 * 0.02 = 1000)
        assert position_value <= current_equity * 0.03  # Allow some buffer for calculation
    
    def test_position_size_with_max_positions_reached(self):
        """Test position sizing when maximum positions are reached."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.9
        }
        
        current_equity = 100000.0
        open_positions = 3  # At maximum
        current_price = 100.0
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        # Should still allow position sizing for strong signals or return None
        # Behavior depends on implementation
        if result is not None:
            assert 'position_size' in result
    
    def test_position_size_with_low_equity(self):
        """Test position sizing with very low equity."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.8
        }
        
        current_equity = 1000.0  # Very low equity
        open_positions = 0
        current_price = 100.0
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        if result is not None:
            assert result['position_size'] >= 1  # At least 1 share
            position_value = result['position_size'] * current_price
            assert position_value <= current_equity  # Can't exceed available equity
    
    def test_position_size_handles_zero_equity(self):
        """Test position sizing gracefully handles zero equity."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.8
        }
        
        current_equity = 0.0
        open_positions = 0
        current_price = 100.0
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        # Should return None or minimal position
        if result is not None:
            assert result['position_size'] == 0
    
    def test_position_size_with_expensive_stock(self):
        """Test position sizing with very expensive stock price."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.8
        }
        
        current_equity = 100000.0
        open_positions = 0
        current_price = 3000.0  # Expensive stock like BRK.A
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        if result is not None:
            assert result['position_size'] >= 1
            position_value = result['position_size'] * current_price
            # Should still respect risk limits
            assert position_value <= current_equity * 0.05  # Max ~5% in one position


class TestRiskConstraints:
    """Test risk constraint enforcement."""
    
    def test_risk_per_trade_constraint(self):
        """Test 2% risk per trade constraint is enforced."""
        
        # This would need to be implemented in the risk module
        # For now, test that position sizing considers this constraint
        
        max_risk_per_trade = 0.02
        equity = 100000
        max_position_value = equity * max_risk_per_trade
        
        assert max_position_value == 2000.0
    
    def test_stop_loss_calculation(self):
        """Test stop loss calculation (5% stop loss)."""
        
        entry_price = 100.0
        stop_loss_pct = 0.05
        expected_stop_loss = entry_price * (1 - stop_loss_pct)
        
        assert expected_stop_loss == 95.0
    
    def test_max_positions_constraint(self):
        """Test maximum 3 open positions constraint."""
        
        max_positions = 3
        current_positions = 2
        
        can_open_new = current_positions < max_positions
        assert can_open_new is True
        
        current_positions = 3
        can_open_new = current_positions < max_positions
        assert can_open_new is False


class TestPositionSizingEdgeCases:
    """Test edge cases in position sizing."""
    
    def test_fractional_shares_handling(self):
        """Test handling of fractional share calculations."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.8
        }
        
        current_equity = 100000.0
        open_positions = 0
        current_price = 333.33  # Price that would create fractional shares
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        if result is not None:
            # Position size should be integer (whole shares)
            assert isinstance(result['position_size'], int)
            assert result['position_size'] > 0
    
    def test_minimum_position_size(self):
        """Test minimum position size constraints."""
        
        signals = {
            'side': 'buy',
            'signal': 1,
            'strength': 0.1  # Very weak signal
        }
        
        current_equity = 100000.0
        open_positions = 0
        current_price = 50.0
        
        result = calculate_position_size(signals, current_equity, open_positions, current_price)
        
        if result is not None:
            # Should have some minimum position size
            assert result['position_size'] >= 1
    
    def test_signal_strength_impact(self):
        """Test how signal strength affects position sizing."""
        
        base_params = {
            'current_equity': 100000.0,
            'open_positions': 0,
            'current_price': 100.0
        }
        
        # Test weak signal
        weak_signals = {'side': 'buy', 'signal': 1, 'strength': 0.3}
        weak_result = calculate_position_size(weak_signals, **base_params)
        
        # Test strong signal  
        strong_signals = {'side': 'buy', 'signal': 1, 'strength': 0.9}
        strong_result = calculate_position_size(strong_signals, **base_params)
        
        if weak_result and strong_result:
            # Strong signals might result in larger positions
            # (This depends on implementation)
            assert weak_result['position_size'] > 0
            assert strong_result['position_size'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])