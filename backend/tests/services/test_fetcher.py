import unittest
import pytest
from backend.app.services.fetcher import fetch_ohlcv, cache, CACHE_TTL
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

class TestDataFetcher:
    @pytest.fixture(autouse=True)
    def setup(self, mock_requests):
        self.mock_get, _ = mock_requests
        # Clear cache before each test
        cache.clear()

    def test_cache_hit(self):
        """Test that subsequent calls for the same symbol use cache."""
        # First call should hit the API
        result1 = fetch_ohlcv("AAPL")
        assert result1 is not None
        assert isinstance(result1, pd.DataFrame)
        assert 'close' in result1.columns

        # Second call should use cache
        result2 = fetch_ohlcv("AAPL")
        assert result2 is not None
        assert isinstance(result2, pd.DataFrame)
        assert 'close' in result2.columns
        
        # Verify only one API call was made
        assert self.mock_get.call_count == 1

    def test_cache_miss(self):
        """Test that different symbols don't use cache."""
        # First symbol
        result1 = fetch_ohlcv("AAPL")
        assert result1 is not None
        assert isinstance(result1, pd.DataFrame)

        # Different symbol should not use cache
        result2 = fetch_ohlcv("MSFT")
        assert result2 is not None
        assert isinstance(result2, pd.DataFrame)
        
        # Verify two API calls were made
        assert self.mock_get.call_count == 2

    def test_cache_expiry(self):
        """Test that cache expires after TTL."""
        # First call
        result1 = fetch_ohlcv("AAPL")
        assert result1 is not None

        # Mock time passing
        with patch('time.time') as mock_time:
            mock_time.return_value = datetime.now().timestamp() + CACHE_TTL + 1
            # Should make new API call after cache expires
            result2 = fetch_ohlcv("AAPL")
            assert result2 is not None
            assert self.mock_get.call_count == 2

    def test_error_handling(self):
        """Test error handling for API failures."""
        # Mock API error
        self.mock_get.side_effect = Exception("API error")
        result = fetch_ohlcv("AAPL")
        assert result is None

class TestFetcher:
    @pytest.fixture(autouse=True)
    def setup(self, mock_requests):
        self.mock_get, _ = mock_requests
        cache.clear()

    def test_fetch_ohlcv_success(self):
        """Test successful data fetching."""
        result = fetch_ohlcv("AAPL")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'close' in result.columns
        assert len(result) > 0

    def test_fetch_ohlcv_failure(self):
        """Test handling of failed API response from both APIs."""
        # Both Tiingo and Alpha Vantage return 400
        def side_effect(url, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {}
            return mock_response
        self.mock_get.side_effect = side_effect
        result = fetch_ohlcv("AAPL")
        assert result is None

    def test_fetch_ohlcv_exception(self):
        """Test handling of network exceptions."""
        self.mock_get.side_effect = Exception("Network error")
        result = fetch_ohlcv("AAPL")
        assert result is None

    def test_fetch_ohlcv_empty_data(self):
        """Test handling of empty API response from both APIs."""
        def side_effect(url, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if 'tiingo' in url.lower():
                mock_response.json.return_value = []
            else:
                mock_response.json.return_value = {'Time Series (Daily)': {}}
            return mock_response
        self.mock_get.side_effect = side_effect
        result = fetch_ohlcv("AAPL")
        assert result is None

    def test_fetch_ohlcv_missing_columns(self):
        """Test handling of API response with missing required columns from both APIs."""
        def side_effect(url, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if 'tiingo' in url.lower():
                mock_response.json.return_value = [
                    {
                        'date': '2024-01-01T00:00:00.000Z',
                        'open': 100.0,
                        'high': 105.0,
                        'low': 95.0
                        # Missing 'close' and 'volume'
                    }
                ]
            else:
                mock_response.json.return_value = {'Time Series (Daily)': {
                    '2024-01-01': {
                        '1. open': '100.0',
                        '2. high': '105.0',
                        '3. low': '95.0'
                        # Missing '4. close' and '5. volume'
                    }
                }}
            return mock_response
        self.mock_get.side_effect = side_effect
        result = fetch_ohlcv("AAPL")
        assert result is None 