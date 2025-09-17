import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd

def test_get_signals_success(client, sample_signals_data, valid_api_key):
    """Test successful signals retrieval."""
    with patch('backend.app.api.endpoints.signals.supabase_db.get_supabase_client') as mock_supabase, \
         patch('backend.app.api.endpoints.signals.fetch_ohlcv') as mock_fetch, \
         patch('backend.app.api.endpoints.signals.generate_signals') as mock_signals:
        
        # Create a complete mock client
        mock_client = MagicMock()
        mock_positions_response = MagicMock()
        mock_positions_response.data = [{'symbol': 'AAPL'}]
        
        mock_client.table.return_value.select.return_value.execute.return_value = mock_positions_response
        mock_supabase.return_value = mock_client
        
        # Mock OHLCV data
        mock_ohlcv = pd.DataFrame({'close': [100], 'SMA20': [95], 'SMA50': [90], 'RSI': [60]})
        mock_ohlcv.index = pd.to_datetime(['2024-01-01'])
        mock_fetch.return_value = mock_ohlcv
        
        # Mock signals
        mock_signals.return_value = {
            'signal': 1,  # BUY
            'strength': 0.75,
            'data': mock_ohlcv
        }
        
        response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
        
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "timestamp" in data
        assert "data_delay_minutes" in data
        assert "AAPL" in data["signals"]
        assert data["signals"]["AAPL"]["signal"] == "BUY"

def test_get_signals_with_symbol(client, mock_supabase, sample_signals_data, valid_api_key):
    """Test signals retrieval for specific symbol."""
    with patch('backend.app.api.endpoints.signals.fetch_ohlcv') as mock_fetch, \
         patch('backend.app.api.endpoints.signals.generate_signals') as mock_signals:
        
        # Mock positions response
        mock_supabase.return_value.table.return_value.select.return_value.execute.return_value.data = [{'symbol': 'AAPL'}]
        
        # Mock OHLCV data
        mock_ohlcv = pd.DataFrame({'close': [100], 'SMA20': [95], 'SMA50': [90], 'RSI': [60]})
        mock_ohlcv.index = pd.to_datetime(['2024-01-01'])
        mock_fetch.return_value = mock_ohlcv
        
        # Mock signals
        mock_signals.return_value = {
            'signal': 1,  # BUY
            'strength': 0.75,
            'data': mock_ohlcv
        }
        
        # Note: The current endpoint doesn't support symbol parameter, it gets symbols from positions
        response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
        
        assert response.status_code == 200
        data = response.json()
        assert "AAPL" in data["signals"]

def test_get_signals_no_data(client, mock_supabase, valid_api_key):
    """Test signals retrieval with no positions (should default to AAPL)."""
    with patch('backend.app.api.endpoints.signals.fetch_ohlcv') as mock_fetch, \
         patch('backend.app.api.endpoints.signals.generate_signals') as mock_signals:
        
        # Mock empty positions response
        mock_supabase.return_value.table.return_value.select.return_value.execute.return_value.data = []
        
        # Mock OHLCV data for default AAPL symbol
        mock_ohlcv = pd.DataFrame({'close': [100], 'SMA20': [95], 'SMA50': [90], 'RSI': [60]})
        mock_ohlcv.index = pd.to_datetime(['2024-01-01'])
        mock_fetch.return_value = mock_ohlcv
        
        # Mock signals
        mock_signals.return_value = {
            'signal': 0,  # HOLD
            'strength': 0.5,
            'data': mock_ohlcv
        }
        
        response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
        
        assert response.status_code == 200
        data = response.json()
        assert "AAPL" in data["signals"]  # Default symbol
        assert data["signals"]["AAPL"]["signal"] == "HOLD"

def test_get_signals_invalid_api_key(client):
    """Test signals retrieval with invalid API key."""
    import os
    # Temporarily disable test mode to test auth
    original_test_mode = os.environ.get('TEST_MODE')
    os.environ['TEST_MODE'] = 'false'
    os.environ['API_KEY'] = 'correct-key'
    
    try:
        response = client.get("/api/signals", headers={"X-API-Key": "invalid_key"})
        assert response.status_code == 403
    finally:
        # Restore test mode
        if original_test_mode:
            os.environ['TEST_MODE'] = original_test_mode
        else:
            os.environ.pop('TEST_MODE', None)

def test_get_signals_database_error(client, mock_supabase, valid_api_key):
    """Test signals retrieval with database error."""
    # Mock database error
    mock_supabase.return_value.table.return_value.select.return_value.execute.side_effect = Exception("Database error")
    
    response = client.get("/api/signals", headers={"X-API-Key": valid_api_key})
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"] 
