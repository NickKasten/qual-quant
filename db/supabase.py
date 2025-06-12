import os
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY or "",
    "Content-Type": "application/json"
}

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
    required_fields = ['symbol', 'quantity', 'avg_entry_price']
    return all(field in position_data for field in required_fields)

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
            return []
    except Exception as e:
        logger.error(f"Error reading trades: {e}")
        return []

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

def update_trades(trade_result: Dict) -> None:
    """
    Write trade result to Supabase/Postgres.
    """
    if not trade_result or not validate_trade_data(trade_result):
        logger.error("Invalid trade data")
        return

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/trades",
            headers=HEADERS,
            json=trade_result
        )
        if response.status_code == 200:
            logger.info("Trade updated successfully")
        else:
            logger.error(f"Failed to update trade: {response.text}")
    except Exception as e:
        logger.error(f"Error updating trade: {e}")

def update_positions(trade_result: Dict) -> None:
    """
    Write position update to Supabase/Postgres.
    """
    if not trade_result or not validate_position_data(trade_result):
        logger.error("Invalid position data")
        return

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/positions",
            headers=HEADERS,
            json=trade_result
        )
        if response.status_code == 200:
            logger.info("Position updated successfully")
        else:
            logger.error(f"Failed to update position: {response.text}")
    except Exception as e:
        logger.error(f"Error updating position: {e}")

def update_equity(trade_result: Dict) -> None:
    """
    Write equity update to Supabase/Postgres.
    """
    if not trade_result or not validate_equity_data(trade_result):
        logger.error("Invalid equity data")
        return

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/equity",
            headers=HEADERS,
            json=trade_result
        )
        if response.status_code == 200:
            logger.info("Equity updated successfully")
        else:
            logger.error(f"Failed to update equity: {response.text}")
    except Exception as e:
        logger.error(f"Error updating equity: {e}") 