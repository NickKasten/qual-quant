import pytest
from datetime import datetime, timedelta
import os
from backend.app.db.supabase import get_supabase_client
from backend.app.core.config import load_config

# Skip integration tests if no Supabase credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"),
    reason="Supabase credentials not available"
)

@pytest.fixture
def supabase():
    """Get real Supabase client for integration tests."""
    return get_supabase_client()

@pytest.fixture
def test_data(supabase):
    """Set up test data in Supabase."""
    # Create test portfolio data
    equity_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "equity": 100000.0
    }
    supabase.table("equity").insert(equity_data).execute()
    
    position_data = {
        "symbol": "AAPL",
        "quantity": 10,
        "avg_entry_price": 150.0,
        "current_price": 155.0,
        "is_open": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    supabase.table("positions").insert(position_data).execute()
    
    trade_data = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10,
        "fill_price": 150.0,
        "timestamp": datetime.utcnow().isoformat(),
        "pnl": 50.0,
        "pnl_pct": 3.33
    }
    supabase.table("trades").insert(trade_data).execute()
    
    signal_data = {
        "symbol": "AAPL",
        "timestamp": datetime.utcnow().isoformat(),
        "signal_type": "SMA",
        "value": 155.0,
        "threshold": 150.0,
        "signal": "BUY",
        "strength": 0.8
    }
    supabase.table("signals").insert(signal_data).execute()
    
    yield
    
    # Clean up test data
    supabase.table("equity").delete().execute()
    supabase.table("positions").delete().execute()
    supabase.table("trades").delete().execute()
    supabase.table("signals").delete().execute()

def test_portfolio_integration(client, test_data, valid_api_key):
    """Test portfolio endpoint with real Supabase."""
    response = client.get("/api/portfolio", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert data["total_equity"] == 100000.0
    assert len(data["positions"]) == 1
    assert data["positions"][0]["symbol"] == "AAPL"

def test_trades_integration(client, test_data, valid_api_key):
    """Test trades endpoint with real Supabase."""
    response = client.get("/api/trades", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) == 1
    assert data["trades"][0]["symbol"] == "AAPL"
    assert data["trades"][0]["side"] == "buy"

def test_performance_integration(client, test_data, valid_api_key):
    """Test performance endpoint with real Supabase."""
    response = client.get("/api/performance", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert len(data["equity_curve"]) > 0
    assert "total_return" in data
    assert "sharpe_ratio" in data
    assert "max_drawdown" in data

def test_signals_integration(client, test_data, valid_api_key):
    """Test signals endpoint with real Supabase."""
    response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert len(data["signals"]) == 1
    assert data["signals"][0]["symbol"] == "AAPL"
    assert data["signals"][0]["signal"] == "BUY"

def test_status_integration(client, test_data, valid_api_key):
    """Test status endpoint with real Supabase."""
    response = client.get("/api/status", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "healthy"
    assert all(c["status"] == "healthy" for c in data["components"].values())

def test_api_rate_limiting(client, valid_api_key):
    """Test API rate limiting."""
    # Make multiple requests in quick succession
    for _ in range(10):
        response = client.get("/api/status", headers={"X-API-Key": valid_api_key})
        assert response.status_code == 200
    
    # The next request should be rate limited
    response = client.get("/api/status", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 429  # Too Many Requests 