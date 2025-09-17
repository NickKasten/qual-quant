
import importlib.util
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, UTC
import pandas as pd

from backend.app.api.main import app

client = TestClient(app)
API_HEADERS = {"X-API-Key": "test-api-key"}
SLOWAPI_AVAILABLE = importlib.util.find_spec("slowapi") is not None

# Mock data
MOCK_POSITIONS = [
    {"symbol": "AAPL", "quantity": 10, "average_entry_price": 150.0, "current_price": 155.0, "unrealized_pnl": 50.0},
]

MOCK_EQUITY = [
    {"equity": 100000.0, "cash": 50000.0, "total_value": 150000.0, "timestamp": (datetime.now(UTC) - timedelta(minutes=15)).isoformat()}
]

MOCK_TRADES = [
    {"symbol": "AAPL", "side": "buy", "quantity": 10, "price": 150.0, "timestamp": datetime.now(UTC).isoformat()},
]

MOCK_SIGNALS = [
    {"symbol": "AAPL", "signal_type": "buy", "strength": 0.8, "strategy": "sma", "price": 155.0}
]

def supabase_mock_factory():
    client = MagicMock()

    def table_side_effect(name: str):
        table_mock = MagicMock()
        if name == "positions":
            table_mock.select.return_value.execute.return_value.data = MOCK_POSITIONS
        elif name == "equity":
            table_mock.select.return_value.order.return_value.limit.return_value.execute.return_value.data = MOCK_EQUITY
            table_mock.select.return_value.gte.return_value.order.return_value.execute.return_value.data = MOCK_EQUITY
        elif name == "trades":
            table_mock.select.return_value.execute.return_value.data = MOCK_TRADES
            table_mock.select.return_value.order.return_value.range.return_value.execute.return_value.data = MOCK_TRADES
        elif name == "signals":
            table_mock.select.return_value.execute.return_value.data = MOCK_SIGNALS
        else:
            table_mock.select.return_value.execute.return_value.data = []
        return table_mock

    client.table.side_effect = table_side_effect
    return client


@patch("backend.app.api.endpoints.portfolio.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
@patch("backend.app.api.endpoints.trades.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
@patch("backend.app.api.endpoints.performance.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
@patch("backend.app.api.endpoints.status.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
def test_health_check(*_):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("backend.app.api.endpoints.portfolio.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_portfolio(_):
    response = client.get("/api/portfolio", headers=API_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert "current_equity" in data
    assert "total_pl" in data


@patch("backend.app.api.endpoints.trades.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_trades(_):
    response = client.get("/api/trades?page=1&page_size=10", headers=API_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "trades" in data
    assert "pagination" in data


@patch("backend.app.api.endpoints.performance.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_performance(_):
    response = client.get("/api/performance?days=30", headers=API_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "equity_curve" in data
    assert "metrics" in data


@patch("backend.app.api.endpoints.signals.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
@patch("backend.app.api.endpoints.signals.fetch_ohlcv")
@patch("backend.app.api.endpoints.signals.generate_signals")
def test_get_signals(mock_generate_signals, mock_fetch_ohlcv, _):
    mock_df = pd.DataFrame({'close': [155.0], 'SMA20': [150.0], 'SMA50': [145.0], 'RSI': [55.0]}, index=[datetime.now(UTC)])
    mock_fetch_ohlcv.return_value = mock_df
    mock_generate_signals.return_value = {
        'signal': 1,
        'side': 'buy',
        'strength': 0.8,
        'data': mock_df
    }
    response = client.get("/api/signals", headers=API_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "signals" in data


@patch("backend.app.api.endpoints.status.supabase_db.get_supabase_client", side_effect=supabase_mock_factory)
def test_get_status(_):
    response = client.get("/api/status", headers=API_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "system_time" in data


def test_rate_limiting():
    if not SLOWAPI_AVAILABLE:
        pytest.skip("slowapi not installed")

    for _ in range(31):
        response = client.get("/api/portfolio", headers=API_HEADERS)
    assert response.status_code == 429
