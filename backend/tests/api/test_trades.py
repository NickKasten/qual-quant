import pytest
from datetime import datetime, timedelta

def test_get_trades_success(client, mock_supabase, sample_trades_data, valid_api_key):
    """Test successful trades retrieval with pagination."""
    # Mock Supabase responses
    mock_supabase.return_value.table.return_value.select.return_value.execute.return_value.data = sample_trades_data
    
    response = client.get("/api/trades?page=1&page_size=20", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert "trades" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert len(data["trades"]) == 1
    assert data["trades"][0]["symbol"] == "AAPL"

def test_get_trades_with_filters(client, mock_supabase, sample_trades_data, valid_api_key):
    """Test trades retrieval with filters."""
    # Mock Supabase responses
    mock_supabase.return_value.table.return_value.select.return_value.execute.return_value.data = sample_trades_data
    
    start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    end_date = datetime.utcnow().isoformat()
    
    response = client.get(
        f"/api/trades?symbol=AAPL&start_date={start_date}&end_date={end_date}",
        headers={"X-API-Key": valid_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) == 1

def test_get_trades_no_data(client, mock_supabase, valid_api_key):
    """Test trades retrieval with no data."""
    # Mock empty Supabase response
    mock_supabase.return_value.table.return_value.select.return_value.execute.return_value.data = []
    
    response = client.get("/api/trades", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) == 0
    assert data["total"] == 0
    assert data["total_pages"] == 0

def test_get_trades_invalid_pagination(client, valid_api_key):
    """Test trades retrieval with invalid pagination parameters."""
    response = client.get("/api/trades?page=0&page_size=20", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 422
    
    response = client.get("/api/trades?page=1&page_size=0", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 422
    
    response = client.get("/api/trades?page=1&page_size=101", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 422

def test_get_trades_invalid_api_key(client):
    """Test trades retrieval with invalid API key."""
    response = client.get("/api/trades", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 403

def test_get_trades_database_error(client, mock_supabase, valid_api_key):
    """Test trades retrieval with database error."""
    # Mock database error
    mock_supabase.return_value.table.return_value.select.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/trades", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"] 