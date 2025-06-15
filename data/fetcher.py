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
    logger.info(f"Processing Tiingo data with {len(data)} records")
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    logger.info(f"Processed Tiingo data shape: {df.shape}")
    return df

def _process_alpha_vantage_data(data: dict) -> pd.DataFrame:
    """Convert Alpha Vantage API response to DataFrame"""
    logger.info("Processing Alpha Vantage data")
    time_series = data.get('Time Series (Daily)', {})
    if not time_series:
        logger.error("No time series data found in Alpha Vantage response")
        return pd.DataFrame()
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.astype(float)
    logger.info(f"Processed Alpha Vantage data shape: {df.shape}")
    return df

def fetch_ohlcv(symbol: str = "AAPL") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from Tiingo (primary) or Alpha Vantage (fallback), with caching.
    Returns a pandas DataFrame with OHLCV data.
    """
    logger.info(f"Fetching OHLCV data for {symbol}")
    
    # Check cache first
    cache_key = f"{symbol}_ohlcv"
    if cache_key in cache and time.time() - cache[cache_key]['timestamp'] < CACHE_TTL:
        logger.info(f"Cache hit for {symbol}, data shape: {cache[cache_key]['data'].shape}")
        return cache[cache_key]['data']
    logger.info("Cache miss, fetching fresh data")

    # Try Tiingo first
    if TIIINGO_API_KEY:
        logger.info("Attempting to fetch from Tiingo API")
        try:
            response = requests.get(
                f"{TIIINGO_BASE_URL}/{symbol}/prices",
                params={"token": TIIINGO_API_KEY, "format": "json"}
            )
            logger.info(f"Tiingo API response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                df = _process_tiingo_data(data)
                if not df.empty:
                    cache[cache_key] = {'data': df, 'timestamp': time.time()}
                    return df
                else:
                    logger.error("Processed Tiingo data is empty")
            else:
                logger.error(f"Tiingo API error: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching from Tiingo: {str(e)}")
    else:
        logger.warning("Tiingo API key not found")

    # Fallback to Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        logger.info("Attempting to fetch from Alpha Vantage API")
        try:
            response = requests.get(
                ALPHA_VANTAGE_BASE_URL,
                params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY}
            )
            logger.info(f"Alpha Vantage API response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return None
                df = _process_alpha_vantage_data(data)
                if not df.empty:
                    cache[cache_key] = {'data': df, 'timestamp': time.time()}
                    return df
                else:
                    logger.error("Processed Alpha Vantage data is empty")
            else:
                logger.error(f"Alpha Vantage API error: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {str(e)}")
    else:
        logger.warning("Alpha Vantage API key not found")

    logger.error("Failed to fetch OHLCV data from both sources")
    return None 