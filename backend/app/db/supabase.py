import os
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, UTC
from supabase import create_client, Client
from ..core.config import load_config

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

HEADERS = {
    "apikey": SUPABASE_KEY or "",
    "Content-Type": "application/json"
}

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Get or create a Supabase client instance.
    Uses singleton pattern to avoid creating multiple clients.
    """
    global _supabase_client
    
    if _supabase_client is None:
        config = load_config()
        url = config.get("SUPABASE_URL")
        key = config.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        _supabase_client = create_client(url, key)
    
    return _supabase_client

def validate_trade_data(trade_data: Dict) -> bool:
    """
    Validate trade data before writing to database.
    """
    required_fields = ['symbol', 'side', 'quantity', 'status', 'order_id']
    return all(field in trade_data for field in required_fields)

def validate_position_data(position_data: Dict) -> bool:
    """
    Validate position data before writing to database.
    """
    required_fields = ['symbol', 'quantity', 'filled_avg_price']
    if not all(field in position_data for field in required_fields):
        return False
    try:
        float(position_data['filled_avg_price'])
        return True
    except (ValueError, TypeError):
        return False

def validate_equity_data(equity_data: Dict) -> bool:
    """
    Validate equity data before writing to database.
    """
    required_fields = ['equity', 'timestamp']
    return all(field in equity_data for field in required_fields)

def setup_tables():
    """
    Set up Supabase/Postgres tables for trades, positions, and equity.
    """
    tables = ["trades", "positions", "equity"]
    for table in tables:
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/create_table",
                headers=HEADERS,
                json={"table_name": table}
            )
            if response.status_code == 200:
                logger.info(f"Table {table} created or already exists.")
            else:
                logger.error(f"Failed to create table {table}: {response.text}")
        except Exception as e:
            logger.error(f"Error setting up table {table}: {e}")

def read_trades(symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    Read trades from Supabase/Postgres.
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/trades"
        params = {"limit": limit}
        if symbol:
            params["symbol"] = f"eq.{symbol}"
            
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to read trades: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error reading trades: {e}")
        return None

def read_positions(symbol: Optional[str] = None) -> List[Dict]:
    """
    Read positions from Supabase/Postgres.
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/positions"
        params = {}
        if symbol:
            params["symbol"] = f"eq.{symbol}"
            
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to read positions: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error reading positions: {e}")
        return []

def read_equity_history(days: int = 30) -> List[Dict]:
    """
    Read equity history from Supabase/Postgres.
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/equity"
        params = {
            "order": "timestamp.desc",
            "limit": days
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to read equity history: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error reading equity history: {e}")
        return []

def update_trades(trade_result: Dict) -> bool:
    """
    Write trade result to Supabase/Postgres.
    Returns True if successful, False otherwise.
    """
    if not trade_result or not validate_trade_data(trade_result):
        logger.error("Invalid trade data")
        return False

    if TEST_MODE:
        logger.info("Test mode: Skipping trade update")
        return True

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/trades",
            headers=HEADERS,
            json=trade_result
        )
        if response.status_code == 200:
            logger.info("Trade updated successfully")
            return True
        else:
            logger.error(f"Failed to update trade: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating trade: {e}")
        return False

def update_positions(trade_result: Dict) -> bool:
    """
    Write position update to Supabase/Postgres.
    Returns True if successful, False otherwise.
    """
    if not trade_result or not validate_position_data(trade_result):
        logger.error("Invalid position data")
        return False

    if TEST_MODE:
        logger.info("Test mode: Skipping position update")
        return True

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/positions",
            headers=HEADERS,
            json=trade_result
        )
        if response.status_code == 200:
            logger.info("Position updated successfully")
            return True
        else:
            logger.error(f"Failed to update position: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        return False

def update_equity(trade_result: Dict) -> bool:
    """
    Write equity update to Supabase/Postgres.
    Returns True if successful, False otherwise.
    """
    if not trade_result or not validate_equity_data(trade_result):
        logger.error("Invalid equity data")
        return False

    if TEST_MODE:
        logger.info("Test mode: Skipping equity update")
        return True

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/equity",
            headers=HEADERS,
            json=trade_result
        )
        if response.status_code == 200:
            logger.info("Equity updated successfully")
            return True
        else:
            logger.error(f"Failed to update equity: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating equity: {e}")
        return False 