import os
import secrets
from fastapi import HTTPException, Header
from typing import Optional

def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def get_api_key_from_env() -> Optional[str]:
    """Get the API key from environment variables."""
    return os.getenv("API_KEY")

def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """
    Verify the provided API key against the configured one.
    
    Args:
        x_api_key: The API key from X-API-Key header
        
    Returns:
        bool: True if valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    expected_api_key = get_api_key_from_env()
    test_mode_env = os.getenv("TEST_MODE", "false").lower()
    
    # In test mode, allow any key or no key
    if test_mode_env == "true":
        return True
    
    if not expected_api_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server"
        )
    
    if not x_api_key:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )
    
    if x_api_key != expected_api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True

