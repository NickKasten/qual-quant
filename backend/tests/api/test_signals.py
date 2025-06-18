import pytest
from datetime import datetime

def test_get_signals_success(client, mock_supabase, sample_signals_data, valid_api_key):
    """Test successful signals retrieval."""
    # Mock Supabase response
    mock_supabase.return_value.table.return_value.select.return_value.order.return_value.execute.return_value.data = sample_signals_data
    
    response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert "signals" in data
    assert "last_updated" in data
    assert "data_delay_minutes" in data
    assert len(data["signals"]) == 1
    assert data["signals"][0]["symbol"] == "AAPL"
    assert data["signals"][0]["signal"] == "BUY"

def test_get_signals_with_symbol(client, mock_supabase, sample_signals_data, valid_api_key):
    """Test signals retrieval for specific symbol."""
    # Mock Supabase response
    mock_supabase.return_value.table.return_value.select.return_value.order.return_value.execute.return_value.data = sample_signals_data
    
    response = client.get("/api/signals?symbol=AAPL", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["signals"]) == 1
    assert data["signals"][0]["symbol"] == "AAPL"

def test_get_signals_no_data(client, mock_supabase, valid_api_key):
    """Test signals retrieval with no data."""
    # Mock empty Supabase response
    mock_supabase.return_value.table.return_value.select.return_value.order.return_value.execute.return_value.data = []
    
    response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 404
    assert response.json()["detail"] == "No signals found"

def test_get_signals_invalid_api_key(client):
    """Test signals retrieval with invalid API key."""
    response = client.get("/api/signals", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 403

def test_get_signals_database_error(client, mock_supabase, valid_api_key):
    """Test signals retrieval with database error."""
    # Mock database error
    mock_supabase.return_value.table.return_value.select.return_value.order.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"] 