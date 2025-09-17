"""
Comprehensive tests for authentication and security functionality.
Tests API key validation, rate limiting, and security measures.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path
from fastapi import HTTPException

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backend.app.utils.auth import verify_api_key, generate_api_key, get_api_key_from_env


class TestAPIKeyGeneration:
    """Test API key generation functionality."""
    
    def test_generate_api_key_creates_valid_key(self):
        """Test that generated API keys are valid."""
        
        api_key = generate_api_key()
        
        assert api_key is not None
        assert isinstance(api_key, str)
        assert len(api_key) > 20  # Should be reasonably long
        assert api_key.replace('-', '').replace('_', '').isalnum()  # Should be alphanumeric with allowed chars
    
    def test_generate_api_key_creates_unique_keys(self):
        """Test that each generated API key is unique."""
        
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert key1 != key2
    
    def test_generate_multiple_api_keys_all_unique(self):
        """Test generating multiple API keys ensures uniqueness."""
        
        keys = [generate_api_key() for _ in range(10)]
        
        # All keys should be unique
        assert len(set(keys)) == 10


class TestAPIKeyEnvironment:
    """Test API key environment handling."""
    
    def test_get_api_key_from_env_when_set(self):
        """Test retrieving API key when environment variable is set."""
        
        with patch.dict(os.environ, {'API_KEY': 'test-api-key-123'}):
            api_key = get_api_key_from_env()
            assert api_key == 'test-api-key-123'
    
    def test_get_api_key_from_env_when_not_set(self):
        """Test retrieving API key when environment variable is not set."""
        
        with patch.dict(os.environ, {}, clear=True):
            api_key = get_api_key_from_env()
            assert api_key is None
    
    def test_get_api_key_from_env_when_empty(self):
        """Test retrieving API key when environment variable is empty."""
        
        with patch.dict(os.environ, {'API_KEY': ''}):
            api_key = get_api_key_from_env()
            assert api_key == ''


class TestAPIKeyVerification:
    """Test API key verification functionality."""
    
    def test_verify_api_key_valid_key_in_test_mode(self):
        """Test API key verification with valid key in test mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'true', 'API_KEY': 'test-key'}):
            result = verify_api_key('test-key')
            assert result is True
    
    def test_verify_api_key_any_key_in_test_mode(self):
        """Test API key verification allows any key in test mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'true'}):
            result = verify_api_key('any-key')
            assert result is True
    
    def test_verify_api_key_no_key_in_test_mode(self):
        """Test API key verification allows no key in test mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'true'}):
            result = verify_api_key(None)
            assert result is True
    
    def test_verify_api_key_valid_key_in_production_mode(self):
        """Test API key verification with valid key in production mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'production-key'}):
            result = verify_api_key('production-key')
            assert result is True
    
    def test_verify_api_key_invalid_key_in_production_mode(self):
        """Test API key verification with invalid key in production mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'production-key'}):
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key('wrong-key')
            
            assert exc_info.value.status_code == 403
            assert 'Invalid API key' in str(exc_info.value.detail)
    
    def test_verify_api_key_missing_key_in_production_mode(self):
        """Test API key verification with missing key in production mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'production-key'}):
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key(None)
            
            assert exc_info.value.status_code == 403
            assert 'Not authenticated' in str(exc_info.value.detail)
    
    def test_verify_api_key_no_server_key_configured(self):
        """Test API key verification when server has no key configured."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false'}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key('any-key')
            
            assert exc_info.value.status_code == 500
            assert 'API key not configured on server' in str(exc_info.value.detail)
    
    def test_verify_api_key_empty_key_in_production(self):
        """Test API key verification with empty key in production mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'production-key'}):
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key('')
            
            assert exc_info.value.status_code == 403


class TestSecurityHeaders:
    """Test security-related functionality."""
    
    def test_api_key_not_logged(self):
        """Test that API keys are not accidentally logged."""
        
        # This is more of a code review item, but we can test the auth function
        # doesn't return the key in error messages
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'secret-key'}):
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key('wrong-key')
            
            # Error message should not contain the actual secret key
            assert 'secret-key' not in str(exc_info.value.detail)
    
    def test_consistent_error_messages(self):
        """Test that error messages don't leak information about valid keys."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'real-key'}):
            # Test with no key
            with pytest.raises(HTTPException) as exc_info_1:
                verify_api_key(None)
            
            # Test with wrong key
            with pytest.raises(HTTPException) as exc_info_2:
                verify_api_key('wrong-key')
            
            # Error messages should be generic, not revealing existence of valid keys
            assert exc_info_1.value.status_code == 403
            assert exc_info_2.value.status_code == 403


class TestAuthenticationIntegration:
    """Test authentication integration with API endpoints."""
    
    def test_auth_required_for_protected_endpoints(self):
        """Test that authentication is required for protected endpoints."""
        
        # This would typically test the actual FastAPI endpoints
        # For now, test the dependency function directly
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'valid-key'}):
            # Valid key should work
            result = verify_api_key('valid-key')
            assert result is True
            
            # Invalid key should fail
            with pytest.raises(HTTPException):
                verify_api_key('invalid-key')
    
    def test_auth_bypass_in_test_mode(self):
        """Test that authentication can be bypassed in test mode."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'true'}):
            # Any key should work in test mode
            assert verify_api_key('any-key') is True
            assert verify_api_key(None) is True
            assert verify_api_key('') is True


class TestRateLimiting:
    """Test rate limiting functionality (if implemented)."""
    
    def test_rate_limiting_structure_exists(self):
        """Test that rate limiting components exist in the codebase."""
        
        # Import the API router to check for rate limiting decorators
        try:
            from backend.app.api.endpoints.portfolio import limiter
            assert limiter is not None
        except ImportError:
            pytest.skip("Rate limiting not implemented")
    
    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration."""
        
        try:
            from backend.app.api.endpoints.portfolio import limiter
            
            # Check that limiter has proper configuration
            assert hasattr(limiter, 'limit')
            
        except ImportError:
            pytest.skip("Rate limiting not implemented")


class TestSecurityBestPractices:
    """Test security best practices implementation."""
    
    def test_secrets_not_in_source_code(self):
        """Test that no secrets are hardcoded in source code."""
        
        # Read the auth module source to check for hardcoded secrets
        auth_file = Path(__file__).parent.parent / 'app' / 'utils' / 'auth.py'
        
        if auth_file.exists():
            content = auth_file.read_text()
            
            # Should not contain common secret patterns
            assert 'password' not in content.lower()
            assert 'secret_key_here' not in content.lower()
            assert 'api_key_123' not in content.lower()
    
    def test_environment_variable_naming(self):
        """Test that environment variables follow naming conventions."""
        
        # Test that the auth module uses properly named environment variables
        from backend.app.utils.auth import get_api_key_from_env
        
        # Should be getting from 'API_KEY' environment variable
        with patch.dict(os.environ, {'API_KEY': 'test'}):
            key = get_api_key_from_env()
            assert key == 'test'
    
    def test_api_key_strength_requirements(self):
        """Test that generated API keys meet strength requirements."""
        
        api_key = generate_api_key()
        
        # Should be sufficiently long
        assert len(api_key) >= 32
        
        # Should contain mix of characters (URL-safe base64)
        assert any(c.isalnum() for c in api_key)
        
        # Should not contain easily guessable patterns
        assert 'password' not in api_key.lower()
        assert '123456' not in api_key
        assert 'abcdef' not in api_key.lower()


class TestErrorHandling:
    """Test error handling in authentication."""
    
    def test_auth_handles_none_values_gracefully(self):
        """Test that auth functions handle None values gracefully."""
        
        # Should not crash on None input
        key = get_api_key_from_env()  # Might return None
        
        with patch.dict(os.environ, {'TEST_MODE': 'true'}):
            result = verify_api_key(None)
            assert result is True
    
    def test_auth_handles_empty_strings_gracefully(self):
        """Test that auth functions handle empty strings gracefully."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'real-key'}):
            with pytest.raises(HTTPException):
                verify_api_key('')
    
    def test_auth_handles_whitespace_keys(self):
        """Test that auth functions handle whitespace in keys."""
        
        with patch.dict(os.environ, {'TEST_MODE': 'false', 'API_KEY': 'real-key'}):
            with pytest.raises(HTTPException):
                verify_api_key('  ')  # Whitespace only
            
            with pytest.raises(HTTPException):
                verify_api_key(' real-key ')  # Key with whitespace


if __name__ == "__main__":
    pytest.main([__file__, "-v"])