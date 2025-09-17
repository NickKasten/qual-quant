import pytest
from datetime import datetime, timedelta, timezone

def test_get_performance_success(client, mock_supabase, valid_api_key):
    """Test successful performance data retrieval."""
    # Mock equity data
    equity_data = [
        {"timestamp": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(), "equity": 100000.0 * (1 + i/100)}
        for i in range(30)
    ]
    mock_supabase.return_value.table.return_value.select.return_value.gte.return_value.order.return_value.execute.return_value.data = equity_data
    
    response = client.get("/api/performance", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert "equity_curve" in data
    assert "metrics" in data
    assert "data_delay_minutes" in data
    assert "initial_equity" in data["metrics"]
    assert "final_equity" in data["metrics"]
    assert "total_return_percent" in data["metrics"]
    assert len(data["equity_curve"]) == 30

def test_get_performance_with_date_range(client, mock_supabase, valid_api_key):
    """Test performance data retrieval with date range."""
    # Mock equity data
    equity_data = [
        {"timestamp": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(), "equity": 100000.0 * (1 + i/100)}
        for i in range(7)
    ]
    mock_supabase.return_value.table.return_value.select.return_value.gte.return_value.order.return_value.execute.return_value.data = equity_data
    
    start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    end_date = datetime.now(timezone.utc).isoformat()
    
    response = client.get(
        f"/api/performance?start_date={start_date}&end_date={end_date}",
        headers={"X-API-Key": valid_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["equity_curve"]) == 7

def test_get_performance_no_data(client, mock_supabase, valid_api_key):
    """Test performance data retrieval with no data."""
    # Mock empty Supabase response
    mock_supabase.return_value.table.return_value.select.return_value.gte.return_value.order.return_value.execute.return_value.data = []
    
    response = client.get("/api/performance", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["equity_curve"]) == 0
    assert data["metrics"]["initial_equity"] == 0
    assert data["metrics"]["final_equity"] == 0

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
    mock_supabase.return_value.table.return_value.select.return_value.gte.return_value.order.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/performance", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"] 
