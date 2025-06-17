from supabase import create_client, Client
from .config import get_db_settings
from typing import Optional

class DatabaseClient:
    """Database client for Supabase operations."""
    _instance: Optional[Client] = None

    @classmethod
    def get_instance(cls) -> Client:
        """Get or create a singleton instance of the Supabase client."""
        if cls._instance is None:
            settings = get_db_settings()
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None 