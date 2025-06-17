from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment variables

@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get cached database settings."""
    return DatabaseSettings() 