import pytest
from datetime import datetime, timedelta

def test_get_status_success(client, mock_supabase, valid_api_key):
    """Test successful status retrieval."""
    # Mock component status responses
    mock_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [{"count": 1}]
    mock_supabase.return_value.table.return_value.select.return_value.gte.return_value.execute.return_value.data = [{"count": 1}]
    
    response = client.get("/api/status", headers={"Authorization": f"Bearer {valid_api_key}"})
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "data_delay_minutes" in data
    assert "last_update" in data
    assert "system_time" in data
    assert "version" in data
    assert "disclaimer" in data
    
    # Check component statuses
    status = data["status"]
    assert "database" in status
    assert "api" in status
    
    # Verify all components are healthy
    assert status["database"] == "healthy"
    assert status["api"] == "healthy"

def test_get_status_degraded(client, mock_supabase, valid_api_key):
    """Test status retrieval with degraded components."""
    # Mock database latency > 1000ms
    mock_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.side_effect = [
        Exception("Slow response"),  # Database check
        [{"count": 0}],  # Trading bot check (no recent trades)
        [{"count": 1}]   # Data fetcher check
    ]
    
    response = client.get("/api/status", headers={"Authorization": f"Bearer {valid_api_key}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "degraded"
    
    components = data["components"]
    assert components["database"]["status"] == "down"
    assert components["trading_bot"]["status"] == "degraded"
    assert components["data_fetcher"]["status"] == "healthy"

def test_get_status_down(client, mock_supabase, valid_api_key):
    """Test status retrieval with down components."""
    # Mock all components down
    mock_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/status", headers={"Authorization": f"Bearer {valid_api_key}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "down"
    
    components = data["components"]
    assert all(c["status"] == "down" for c in components.values())

def test_get_status_invalid_api_key(client):
    """Test status retrieval with invalid API key."""
    response = client.get("/api/status", headers={"Authorization": "Bearer invalid_key"})
    assert response.status_code == 401

def test_get_status_database_error(client, mock_supabase, valid_api_key):
    """Test status retrieval with database error."""
    # Mock database error
    mock_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/status", headers={"Authorization": f"Bearer {valid_api_key}"})
    
    assert response.status_code == 200  # Status endpoint should handle errors gracefully
    data = response.json()
    assert data["overall_status"] == "down" 