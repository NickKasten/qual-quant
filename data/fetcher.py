import os
import logging
import requests
import time
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)

TIIINGO_API_KEY = os.getenv("TIIINGO_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
TIIINGO_BASE_URL = "https://api.tiingo.com/tiingo/daily"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Simple in-memory cache
cache = {}
CACHE_TTL = 300  # 5 minutes

def _process_tiingo_data(data: list) -> pd.DataFrame:
    """Convert Tiingo API response to DataFrame"""
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def _process_alpha_vantage_data(data: dict) -> pd.DataFrame:
    """Convert Alpha Vantage API response to DataFrame"""
    time_series = data.get('Time Series (Daily)', {})
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.astype(float)
    return df

def fetch_ohlcv(symbol: str = "AAPL") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from Tiingo (primary) or Alpha Vantage (fallback), with caching.
    Returns a pandas DataFrame with OHLCV data.
    """
    # Check cache first
    cache_key = f"{symbol}_ohlcv"
    if cache_key in cache and time.time() - cache[cache_key]['timestamp'] < CACHE_TTL:
        logger.info(f"Cache hit for {symbol}")
        return cache[cache_key]['data']

    # Try Tiingo first
    if TIIINGO_API_KEY:
        try:
            response = requests.get(
                f"{TIIINGO_BASE_URL}/{symbol}/prices",
                params={"token": TIIINGO_API_KEY, "format": "json"}
            )
            if response.status_code == 200:
                data = response.json()
                df = _process_tiingo_data(data)
                cache[cache_key] = {'data': df, 'timestamp': time.time()}
                return df
        except Exception as e:
            logger.error(f"Error fetching from Tiingo: {e}")

    # Fallback to Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        try:
            response = requests.get(
                ALPHA_VANTAGE_BASE_URL,
                params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY}
            )
            if response.status_code == 200:
                data = response.json()
                df = _process_alpha_vantage_data(data)
                cache[cache_key] = {'data': df, 'timestamp': time.time()}
                return df
        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")

    logger.error("Failed to fetch OHLCV data from both sources")
    return None 