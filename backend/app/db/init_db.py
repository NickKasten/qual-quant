import logging
from typing import Optional
from datetime import datetime, UTC
from .client import DatabaseClient
from .models import Trade, Position, Equity, Signal
from ..core.config import load_config

logger = logging.getLogger(__name__)

def init_database() -> bool:
    """
    Initialize the database with required tables and initial data.
    Returns True if successful, False otherwise.
    """
    try:
        client = DatabaseClient.get_instance()
        settings = load_config()
        
        # Create tables if they don't exist
        _create_tables(client)
        
        # Initialize equity if not exists
        _init_equity(client, float(settings["STARTING_EQUITY"]))
        
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False

def _create_tables(client) -> None:
    """Create database tables if they don't exist."""
    try:
        # Create trades table
        client.table('trades').select('count').limit(1).execute()
        logger.info("Trades table exists")
    except Exception:
        logger.info("Creating trades table...")
        client.table('trades').create().execute()
    
    try:
        # Create positions table
        client.table('positions').select('count').limit(1).execute()
        logger.info("Positions table exists")
    except Exception:
        logger.info("Creating positions table...")
        client.table('positions').create().execute()
    
    try:
        # Create equity table
        client.table('equity').select('count').limit(1).execute()
        logger.info("Equity table exists")
    except Exception:
        logger.info("Creating equity table...")
        client.table('equity').create().execute()
    
    try:
        # Create signals table
        client.table('signals').select('count').limit(1).execute()
        logger.info("Signals table exists")
    except Exception:
        logger.info("Creating signals table...")
        client.table('signals').create().execute()

def _init_equity(client, starting_equity: float) -> None:
    """Initialize equity table with starting value if empty."""
    try:
        result = client.table('equity').select('count').execute()
        if result.data[0]['count'] == 0:
            initial_equity = Equity(
                timestamp=datetime.now(UTC),
                equity=starting_equity,
                cash=starting_equity,
                total_value=starting_equity
            )
            client.table('equity').insert(initial_equity.model_dump()).execute()
            logger.info(f"Initialized equity with {starting_equity}")
    except Exception as e:
        logger.error(f"Failed to initialize equity: {e}")
        raise

def reset_database() -> bool:
    """
    Reset the database by dropping all tables and reinitializing.
    Use with caution!
    """
    try:
        client = DatabaseClient.get_instance()
        
        # Drop tables
        tables = ['trades', 'positions', 'equity', 'signals']
        for table in tables:
            try:
                client.table(table).drop().execute()
                logger.info(f"Dropped table {table}")
            except Exception as e:
                logger.warning(f"Failed to drop table {table}: {e}")
        
        # Reinitialize
        return init_database()
    except Exception as e:
        logger.error(f"Database reset failed: {e}", exc_info=True)
        return False 