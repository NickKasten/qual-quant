import pytest
from datetime import datetime
from unittest.mock import MagicMock

def test_get_portfolio_success(client, mock_supabase, sample_portfolio_data, valid_api_key):
    """Test successful portfolio retrieval."""
    # Mock positions response
    mock_positions_response = MagicMock()
    mock_positions_response.data = sample_portfolio_data["positions"]
    
    # Mock equity response
    mock_equity_response = MagicMock()
    mock_equity_response.data = sample_portfolio_data["equity"]
    
    # Setup complex mock chain for positions
    mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_positions_response
    
    # Setup complex mock chain for equity (different call pattern)
    equity_chain = mock_supabase.return_value.table.return_value.select.return_value.order.return_value.limit
    equity_chain.return_value.execute.return_value = mock_equity_response
    
    response = client.get("/api/portfolio", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert "current_equity" in data
    assert "total_pl" in data
    assert "positions" in data
    assert "timestamp" in data
    assert "data_delay_minutes" in data
    assert "disclaimer" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["symbol"] == "AAPL"

def test_get_portfolio_no_data(client, mock_supabase, valid_api_key):
    """Test portfolio retrieval with no data."""
    # Mock empty responses
    mock_empty_response = MagicMock()
    mock_empty_response.data = []
    
    # Setup mock chain for positions
    mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_empty_response
    
    # Setup mock chain for equity
    equity_chain = mock_supabase.return_value.table.return_value.select.return_value.order.return_value.limit
    equity_chain.return_value.execute.return_value = mock_empty_response
    
    response = client.get("/api/portfolio", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["positions"]) == 0
    assert data["current_equity"] == 0

def test_get_portfolio_invalid_api_key(client):
    """Test portfolio retrieval with invalid API key."""
    response = client.get("/api/portfolio", headers={"X-API-Key": "invalid_key"})
    
    assert response.status_code == 403

def test_get_portfolio_missing_api_key(client):
    """Test portfolio retrieval without API key."""
    response = client.get("/api/portfolio")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"

def test_get_portfolio_database_error(client, mock_supabase, valid_api_key):
    """Test portfolio retrieval with database error."""
    # Mock database error
    mock_supabase.return_value.table.return_value.select.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/portfolio", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"] 