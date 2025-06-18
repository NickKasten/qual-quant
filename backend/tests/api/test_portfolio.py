import pytest
from datetime import datetime
from unittest.mock import MagicMock

def test_get_portfolio_success(client, mock_supabase, sample_portfolio_data, valid_api_key):
    """Test successful portfolio retrieval."""
    # Mock Supabase responses
    mock_supabase.return_value.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = sample_portfolio_data["equity"]
    mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = sample_portfolio_data["positions"]
    
    response = client.get("/api/portfolio", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert "total_equity" in data
    assert "cash" in data
    assert "positions" in data
    assert "last_updated" in data
    assert "data_delay_minutes" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["symbol"] == "AAPL"

def test_get_portfolio_no_data(client, mock_supabase, valid_api_key):
    """Test portfolio retrieval with no data."""
    # Mock empty Supabase responses
    mock_supabase.return_value.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    
    response = client.get("/api/portfolio", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 404
    assert response.json()["detail"] == "No equity data found"

def test_get_portfolio_invalid_api_key(client):
    """Test portfolio retrieval with invalid API key."""
    response = client.get("/api/portfolio", headers={"X-API-Key": "invalid_key"})
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid API key"

def test_get_portfolio_missing_api_key(client):
    """Test portfolio retrieval without API key."""
    response = client.get("/api/portfolio")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"

def test_get_portfolio_database_error(client, mock_supabase, valid_api_key):
    """Test portfolio retrieval with database error."""
    # Mock database error
    mock_supabase.return_value.table.return_value.select.return_value.order.return_value.limit.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/portfolio", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"] 