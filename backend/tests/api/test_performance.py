import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

def _build_equity_series(days: int) -> list:
    base_time = datetime.now(timezone.utc)
    return [
        {"timestamp": (base_time - timedelta(days=days - 1 - i)).isoformat(), "equity": 100000.0 + (i * 500)}
        for i in range(days)
    ]


def _build_benchmark_df(days: int):
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    return pd.DataFrame({
        'open': 100.0,
        'high': 105.0,
        'low': 95.0,
        'close': [410.0 + i for i in range(days)],
        'volume': 1000000
    }, index=dates)


def test_get_performance_success(client, mock_supabase, valid_api_key):
    """Test successful performance data retrieval."""
    equity_data = _build_equity_series(30)

    query_mock = mock_supabase.return_value.table.return_value
    query_mock.execute.return_value = MagicMock(data=equity_data)

    benchmark_df = _build_benchmark_df(30)

    with patch('backend.app.api.endpoints.performance.fetch_ohlcv', return_value=benchmark_df):
        response = client.get("/api/performance", headers={"X-API-Key": valid_api_key})

    assert response.status_code == 200
    data = response.json()
    assert "equity_curve" in data
    assert "metrics" in data
    assert "benchmark_curve" in data
    assert len(data["equity_curve"]) == 30
    assert len(data["benchmark_curve"]) > 0
    assert "data_delay_minutes" in data
    assert "initial_equity" in data["metrics"]
    assert "final_equity" in data["metrics"]
    assert "total_return_percent" in data["metrics"]
    assert len(data["equity_curve"]) == 30

def test_get_performance_days_parameter(client, mock_supabase, valid_api_key):
    """Test performance data retrieval respecting the days parameter."""
    equity_data = _build_equity_series(7)

    query_mock = mock_supabase.return_value.table.return_value
    query_mock.execute.return_value = MagicMock(data=equity_data)

    benchmark_df = _build_benchmark_df(7)

    with patch('backend.app.api.endpoints.performance.fetch_ohlcv', return_value=benchmark_df):
        response = client.get("/api/performance?days=7", headers={"X-API-Key": valid_api_key})

    assert response.status_code == 200
    data = response.json()
    assert len(data["equity_curve"]) == 7

def test_get_performance_no_data(client, mock_supabase, valid_api_key):
    """Test performance data retrieval with no data."""
    # Mock empty Supabase response
    query_mock = mock_supabase.return_value.table.return_value
    query_mock.execute.return_value = MagicMock(data=[])
    
    with patch('backend.app.api.endpoints.performance.fetch_ohlcv', return_value=None):
        response = client.get("/api/performance", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["equity_curve"]) == 0
    assert data["metrics"]["initial_equity"] == pytest.approx(100000.0)
    assert data["metrics"]["final_equity"] == pytest.approx(100000.0)


def test_get_performance_fallback_recent_records(client, mock_supabase, valid_api_key):
    """Ensure the endpoint falls back to most recent equity rows when window is empty."""
    fallback_data = _build_equity_series(5)

    query_mock = mock_supabase.return_value.table.return_value
    query_mock.execute.side_effect = [
        MagicMock(data=[]),
        MagicMock(data=fallback_data)
    ]

    benchmark_df = _build_benchmark_df(5)

    try:
        with patch('backend.app.api.endpoints.performance.fetch_ohlcv', return_value=benchmark_df):
            response = client.get("/api/performance?days=5", headers={"X-API-Key": valid_api_key})
    finally:
        query_mock.execute.side_effect = None

    assert response.status_code == 200
    data = response.json()
    assert len(data["equity_curve"]) == 5
    assert data["benchmark_curve"]

def test_get_performance_invalid_date_range(client, valid_api_key):
    """Test performance data retrieval with invalid date range."""
    # Test with invalid days parameter
    response = client.get(
        "/api/performance?days=500",  # More than max 365
        headers={"X-API-Key": valid_api_key}
    )
    
    assert response.status_code == 422

def test_get_performance_invalid_api_key(client, monkeypatch):
    """Test performance data retrieval with invalid API key."""
    monkeypatch.setenv("TEST_MODE", "false")
    monkeypatch.setenv("API_KEY", "expected-key")
    response = client.get("/api/performance", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 403

def test_get_performance_database_error(client, mock_supabase, valid_api_key):
    """Test performance data retrieval with database error."""
    # Mock database error
    query_mock = mock_supabase.return_value.table.return_value
    query_mock.execute.side_effect = Exception("Database error")
    
    with patch('backend.app.api.endpoints.performance.fetch_ohlcv', return_value=None):
        response = client.get("/api/performance", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"] 
