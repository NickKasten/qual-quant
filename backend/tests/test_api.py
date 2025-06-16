import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, UTC
from app.api.main import app

client = TestClient(app)

# Mock data
MOCK_POSITIONS = [
    {"symbol": "AAPL", "quantity": 10, "avg_price": 150.0, "unrealized_pl": 100.0},
    {"symbol": "GOOGL", "quantity": 5, "avg_price": 2800.0, "unrealized_pl": -200.0}
]

MOCK_EQUITY = [
    {"equity": 100000.0, "timestamp": (datetime.now(UTC) - timedelta(minutes=15)).isoformat()}
]

MOCK_TRADES = [
    {"symbol": "AAPL", "side": "buy", "quantity": 10, "price": 150.0, "timestamp": datetime.now(UTC).isoformat()},
    {"symbol": "GOOGL", "side": "sell", "quantity": 5, "price": 2800.0, "timestamp": datetime.now(UTC).isoformat()}
]

def supabase_mock_factory():
    client = MagicMock()
    # trades endpoint
    client.table.return_value.select.return_value.count.return_value.execute.return_value.count = 2
    client.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value.data = MOCK_TRADES
    # portfolio endpoint
    client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = MOCK_EQUITY
    client.table.return_value.select.return_value.execute.return_value.data = MOCK_POSITIONS
    # performance endpoint
    client.table.return_value.select.return_value.gte.return_value.order.return_value.execute.return_value.data = MOCK_EQUITY
    # status endpoint
    client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = MOCK_EQUITY
    return client

@patch("app.api.endpoints.portfolio.get_supabase_client", side_effect=supabase_mock_factory)
@patch("app.api.endpoints.trades.get_supabase_client", side_effect=supabase_mock_factory)
@patch("app.api.endpoints.performance.get_supabase_client", side_effect=supabase_mock_factory)
@patch("app.api.endpoints.status.get_supabase_client", side_effect=supabase_mock_factory)
def test_health_check(*_):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("app.api.endpoints.portfolio.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_portfolio(_):
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert "current_equity" in data
    assert "total_pl" in data
    assert "data_delay_minutes" in data

@patch("app.api.endpoints.trades.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_trades(_):
    response = client.get("/api/trades?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "trades" in data
    assert "pagination" in data
    assert "data_delay_minutes" in data

@patch("app.api.endpoints.performance.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_performance(_):
    response = client.get("/api/performance?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "equity_curve" in data
    assert "metrics" in data
    assert "data_delay_minutes" in data

@patch("app.api.endpoints.signals.get_supabase_client", side_effect=supabase_mock_factory)
@patch("app.api.endpoints.signals.fetch_ohlcv")
@patch("app.api.endpoints.signals.generate_signals")
def test_get_signals(mock_generate_signals, mock_fetch_ohlcv, _):
    mock_fetch_ohlcv.return_value = MagicMock(empty=False, index=[datetime.now(UTC)])
    mock_generate_signals.return_value = {"side": "buy", "signal": "SMA_CROSS"}
    response = client.get("/api/signals")
    assert response.status_code == 200
    data = response.json()
    assert "signals" in data
    assert "timestamp" in data
    assert "data_delay_minutes" in data

@patch("app.api.endpoints.status.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_status(_):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "last_update" in data
    assert "system_time" in data
    assert "version" in data

def test_rate_limiting():
    # Make multiple requests in quick succession
    for _ in range(31):
        response = client.get("/api/portfolio")
    assert response.status_code == 429  # Too Many Requests 