import os
import secrets
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# Initialize the security scheme
security = HTTPBearer()

def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def get_api_key_from_env() -> Optional[str]:
    """Get the API key from environment variables."""
    return os.getenv("API_KEY")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """
    Verify the provided API key against the configured one.
    
    Args:
        credentials: The HTTP Bearer token credentials
        
    Returns:
        bool: True if valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    expected_api_key = get_api_key_from_env()
    
    if not expected_api_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server"
        )
    
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required. Include 'Authorization: Bearer YOUR_API_KEY' header"
        )
    
    if credentials.credentials != expected_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return True

def verify_api_key_optional(credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False)) -> bool:
    """
    Optional API key verification for endpoints that can work with or without auth.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        bool: True if valid API key provided or no API key configured, False if invalid
    """
    expected_api_key = get_api_key_from_env()
    
    # If no API key is configured, allow access
    if not expected_api_key:
        return True
    
    # If no credentials provided but API key is configured, deny access
    if not credentials or not credentials.credentials:
        return False
    
    # Verify the provided API key
    return credentials.credentials == expected_api_key