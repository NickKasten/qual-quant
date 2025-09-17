import pytest
from datetime import datetime, timedelta


def test_get_trades_success(client, mock_supabase, sample_trades_data, valid_api_key):
    """Test successful trades retrieval with pagination."""
    table = mock_supabase.return_value.table.return_value
    table.select.return_value.execute.return_value.data = sample_trades_data
    table.select.return_value.order.return_value.range.return_value.execute.return_value.data = sample_trades_data
    table.select.return_value.eq.return_value.execute.return_value.data = sample_trades_data
    table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.data = sample_trades_data

    response = client.get("/api/trades?page=1&page_size=20", headers={"X-API-Key": valid_api_key})

    assert response.status_code == 200
    data = response.json()
    assert "trades" in data
    assert "pagination" in data
    assert len(data["trades"]) == 1
    assert data["trades"][0]["symbol"] == "AAPL"
    assert data["pagination"]["page"] == 1


def test_get_trades_with_filters(client, mock_supabase, sample_trades_data, valid_api_key):
    """Test trades retrieval with symbol filter."""
    table = mock_supabase.return_value.table.return_value
    table.select.return_value.execute.return_value.data = sample_trades_data
    table.select.return_value.order.return_value.range.return_value.execute.return_value.data = sample_trades_data
    table.select.return_value.eq.return_value.execute.return_value.data = sample_trades_data
    table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.data = sample_trades_data

    response = client.get(
        "/api/trades?symbol=AAPL",
        headers={"X-API-Key": valid_api_key}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) == 1


def test_get_trades_no_data(client, mock_supabase, valid_api_key):
    """Test trades retrieval with no data."""
    table = mock_supabase.return_value.table.return_value
    table.select.return_value.execute.return_value.data = []
    table.select.return_value.order.return_value.range.return_value.execute.return_value.data = []

    response = client.get("/api/trades", headers={"X-API-Key": valid_api_key})

    assert response.status_code == 200
    data = response.json()
    assert data["trades"] == []
    assert data["pagination"]["total_count"] == 0


def test_get_trades_invalid_pagination(client, valid_api_key):
    """Test trades retrieval with invalid pagination parameters."""
    response = client.get("/api/trades?page=0&page_size=20", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 422

    response = client.get("/api/trades?page=1&page_size=0", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 422

    response = client.get("/api/trades?page=1&page_size=101", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 422


def test_get_trades_invalid_api_key(client, monkeypatch):
    """Test trades retrieval with invalid API key."""
    monkeypatch.setenv("TEST_MODE", "false")
    monkeypatch.setenv("API_KEY", "expected-key")
    response = client.get("/api/trades", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 403


def test_get_trades_database_error(client, mock_supabase, valid_api_key):
    """Test trades retrieval with database error."""
    table = mock_supabase.return_value.table.return_value
    table.select.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Database error")

    response = client.get("/api/trades", headers={"X-API-Key": valid_api_key})

    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]
