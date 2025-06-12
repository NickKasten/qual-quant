import os
import logging
import requests
from typing import Dict

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY or "",
    "Content-Type": "application/json"
}

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

def update_trades(trade_result: Dict) -> None:
    """
    Write trade result to Supabase/Postgres.
    """
    if not trade_result:
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
    if not trade_result:
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
    if not trade_result:
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