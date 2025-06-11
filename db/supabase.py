import os
import logging
import requests
from typing import Dict

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def update_trades(trade_result: Dict) -> None:
    """
    Write trade result to Supabase/Postgres.
    """
    if not trade_result:
        return

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/trades",
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
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
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
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
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
            json=trade_result
        )
        if response.status_code == 200:
            logger.info("Equity updated successfully")
        else:
            logger.error(f"Failed to update equity: {response.text}")
    except Exception as e:
        logger.error(f"Error updating equity: {e}") 