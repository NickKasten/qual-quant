import pytest
from datetime import datetime, timedelta
import os
from app.db.models import Trade, Position, Equity, Signal
from app.db.operations import DatabaseOperations
from app.db.client import DatabaseClient

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["SUPABASE_URL"] = "https://hekzbqywzhdzjiouoeid.supabase.co"
    os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhla3picXl3emhkemppb3VvZWlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4Njg2MjcsImV4cCI6MjA2NTQ0NDYyN30.HX6JzejxJ4eWHC2OPP44ktgwCaHrKI00jtGZitP-NWM"
    yield
    DatabaseClient.reset_instance()

@pytest.fixture
def db_ops():
    """Fixture for database operations."""
    return DatabaseOperations()

def test_create_and_get_trade(db_ops):
    """Test creating and retrieving a trade."""
    trade = Trade(
        symbol="AAPL",
        side="buy",
        quantity=10.0,
        price=150.0,
        strategy="sma_crossover"
    )
    
    created_trade = db_ops.create_trade(trade)
    assert created_trade.symbol == trade.symbol
    assert created_trade.side == trade.side
    assert created_trade.quantity == trade.quantity
    assert created_trade.price == trade.price
    
    trades = db_ops.get_trades(symbol="AAPL")
    assert len(trades) > 0
    assert trades[0].symbol == "AAPL"

def test_position_operations(db_ops):
    """Test position operations."""
    position = Position(
        symbol="AAPL",
        quantity=10.0,
        average_entry_price=150.0,
        current_price=155.0,
        unrealized_pnl=50.0
    )
    
    created_position = db_ops.update_position(position)
    assert created_position.symbol == position.symbol
    assert created_position.quantity == position.quantity
    
    positions = db_ops.get_positions()
    assert len(positions) > 0
    assert positions[0].symbol == "AAPL"

def test_equity_operations(db_ops):
    """Test equity operations."""
    equity = Equity(
        equity=10000.0,
        cash=5000.0,
        total_value=15000.0
    )
    
    created_equity = db_ops.record_equity(equity)
    assert created_equity.equity == equity.equity
    assert created_equity.cash == equity.cash
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    equity_history = db_ops.get_equity_history(start_time, end_time)
    assert len(equity_history) > 0

def test_signal_operations(db_ops):
    """Test signal operations."""
    signal = Signal(
        symbol="AAPL",
        signal_type="buy",
        strength=0.8,
        strategy="sma_crossover",
        price=150.0
    )
    
    created_signal = db_ops.create_signal(signal)
    assert created_signal.symbol == signal.symbol
    assert created_signal.signal_type == signal.signal_type
    
    signals = db_ops.get_latest_signals(symbol="AAPL")
    assert len(signals) > 0
    assert signals[0].symbol == "AAPL" 