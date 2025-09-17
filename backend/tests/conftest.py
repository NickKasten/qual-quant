import os
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timezone
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load .env file from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables before each test."""
    # Set all required environment variables
    env_vars = {
        'TIINGO_API_KEY': 'test_tiingo_key',
        'ALPHA_VANTAGE_API_KEY': 'test_alpha_vantage_key',
        'ALPACA_API_KEY': 'test_alpaca_key',
        'ALPACA_SECRET_KEY': 'test_alpaca_secret',
        'SUPABASE_URL': os.environ.get('SUPABASE_URL', 'test_supabase_url'),
        'SUPABASE_KEY': os.environ.get('SUPABASE_KEY', 'test_supabase_key'),
        'API_KEY': 'test-api-key',
        'TEST_MODE': 'true',
        'MAX_POSITIONS': '3',
        'RISK_PER_TRADE': '0.02',
        'STOP_LOSS_PCT': '0.05'
    }
    
    # Store original values
    original_env = {}
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key in env_vars:
        if key in original_env and original_env[key] is not None:
            os.environ[key] = original_env[key]
        else:
            os.environ.pop(key, None)

@pytest.fixture
def mock_requests():
    """Mock requests for all external API calls."""
    with patch('backend.app.services.fetcher.requests.get') as mock_get, \
         patch('backend.app.services.fetcher.requests.post') as mock_post:
        
        # Mock Tiingo API response
        mock_tiingo_response = MagicMock()
        mock_tiingo_response.status_code = 200
        mock_tiingo_response.json.return_value = [
            {
                'date': '2024-01-01T00:00:00.000Z',
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 1000000
            }
        ]
        
        # Mock Alpha Vantage API response
        mock_av_response = MagicMock()
        mock_av_response.status_code = 200
        mock_av_response.json.return_value = {
            'Time Series (Daily)': {
                '2024-01-01': {
                    '1. open': '100.0',
                    '2. high': '105.0',
                    '3. low': '95.0',
                    '4. close': '102.0',
                    '5. volume': '1000000'
                }
            }
        }
        
        # Mock Alpaca API responses
        mock_alpaca_response = MagicMock()
        mock_alpaca_response.status_code = 200
        mock_alpaca_response.json.return_value = {
            'id': 'test_order_id',
            'status': 'filled',
            'filled_avg_price': '102.0',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Configure mock responses
        mock_get.side_effect = lambda url, **kwargs: (
            mock_tiingo_response if 'tiingo' in url.lower()
            else mock_av_response if 'alphavantage' in url.lower()
            else MagicMock(status_code=200)
        )
        
        mock_post.side_effect = lambda url, **kwargs: (
            mock_alpaca_response if 'alpaca' in url.lower()
            else MagicMock(status_code=200)
        )
        
        yield mock_get, mock_post

@pytest.fixture
def mock_supabase():
    """Mock Supabase database operations."""
    with patch('app.db.supabase.get_supabase_client') as mock_client:
        # Create a flexible mock client that handles any query chain
        mock_supabase_client = MagicMock()
        
        # Create a flexible mock that returns itself for all methods
        # This allows any chaining pattern to work
        flexible_mock = MagicMock()
        flexible_mock.data = []  # Default empty data
        
        # The flexible mock returns itself for any method call
        flexible_mock.table.return_value = flexible_mock
        flexible_mock.select.return_value = flexible_mock
        flexible_mock.gte.return_value = flexible_mock
        flexible_mock.lte.return_value = flexible_mock
        flexible_mock.order.return_value = flexible_mock
        flexible_mock.limit.return_value = flexible_mock
        flexible_mock.execute.return_value = flexible_mock
        flexible_mock.insert.return_value = flexible_mock
        flexible_mock.upsert.return_value = flexible_mock
        flexible_mock.update.return_value = flexible_mock
        flexible_mock.delete.return_value = flexible_mock
        flexible_mock.eq.return_value = flexible_mock
        flexible_mock.neq.return_value = flexible_mock
        flexible_mock.gt.return_value = flexible_mock
        flexible_mock.lt.return_value = flexible_mock
        flexible_mock.like.return_value = flexible_mock
        flexible_mock.ilike.return_value = flexible_mock
        flexible_mock.is_.return_value = flexible_mock
        flexible_mock.filter.return_value = flexible_mock
        
        # Make the client return this flexible mock
        mock_supabase_client.table.return_value = flexible_mock
        mock_client.return_value = mock_supabase_client
        
        yield mock_client

@pytest.fixture
def sample_ohlcv_data():
    """Provide sample OHLCV data for testing."""
    return pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
        'open': 100.0,
        'high': 105.0,
        'low': 95.0,
        'close': 102.0,
        'volume': 1000000
    }).set_index('date')

@pytest.fixture
def sample_trade_data():
    """Provide sample trade data for testing."""
    return {
        'symbol': 'AAPL',
        'side': 'buy',
        'quantity': 10,
        'status': 'filled',
        'order_id': 'test123',
        'filled_avg_price': 102.0,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'simulated': True
    }

@pytest.fixture
def sample_position_data():
    """Provide sample position data for testing."""
    return {
        'symbol': 'AAPL',
        'quantity': 10,
        'entry_price': 102.0,
        'current_price': 102.0,
        'unrealized_pnl': 0.0,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@pytest.fixture
def sample_portfolio_data():
    """Provide sample portfolio data for testing."""
    return {
        'positions': [
            {
                'symbol': 'AAPL',
                'quantity': 10,
                'average_entry_price': 102.0,
                'current_price': 105.0,
                'unrealized_pnl': 30.0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ],
        'equity': [
            {
                'equity': 101000.0,
                'cash': 90000.0,
                'total_value': 101000.0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
    }

@pytest.fixture
def sample_signals_data():
    """Provide sample signals data for testing."""
    return [
        {
            'symbol': 'AAPL',
            'signal': 'BUY',
            'confidence': 0.75,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'price_target': 110.0,
            'stop_loss': 95.0
        },
        {
            'symbol': 'MSFT',
            'signal': 'HOLD',
            'confidence': 0.60,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'price_target': 300.0,
            'stop_loss': 250.0
        }
    ]

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from backend.app.api.main import app
    return TestClient(app)

@pytest.fixture
def valid_api_key():
    """Provide a valid API key for testing."""
    return "test-api-key" 