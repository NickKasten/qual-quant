import os
import logging
import requests
import time
import pandas as pd
from typing import Optional
import tenacity

logger = logging.getLogger(__name__)

TIINGO_BASE_URL = "https://api.tiingo.com/tiingo/daily"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Simple in-memory cache
cache = {}
CACHE_TTL = 300  # 5 minutes

def _get_api_keys():
    """Get API keys from environment variables."""
    return {
        'tiingo': os.getenv("TIINGO_API_KEY"),
        'alpha_vantage': os.getenv("ALPHA_VANTAGE_API_KEY")
    }

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

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    reraise=True,
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
)
def _fetch_tiingo(symbol, api_key):
    response = requests.get(
        f"{TIINGO_BASE_URL}/{symbol}/prices",
        params={"token": api_key, "format": "json"}
    )
    logger.info(f"Tiingo API response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        df = _process_tiingo_data(data)
        return df
    else:
        logger.error(f"Tiingo API error: {response.text}")
        raise Exception("Tiingo API error")

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    reraise=True,
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
)
def _fetch_alpha_vantage(symbol, api_key):
    response = requests.get(
        ALPHA_VANTAGE_BASE_URL,
        params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": api_key}
    )
    logger.info(f"Alpha Vantage API response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if 'Error Message' in data:
            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
            raise Exception("Alpha Vantage API error")
        df = _process_alpha_vantage_data(data)
        return df
    else:
        logger.error(f"Alpha Vantage API error: {response.text}")
        raise Exception("Alpha Vantage API error")

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

    # Get API keys
    api_keys = _get_api_keys()
    required_cols = {'open', 'high', 'low', 'close', 'volume'}

    # Try Tiingo first
    if api_keys['tiingo']:
        logger.info("Attempting to fetch from Tiingo API with retry")
        try:
            df = _fetch_tiingo(symbol, api_keys['tiingo'])
            if not df.empty and required_cols.issubset(df.columns):
                cache[cache_key] = {'data': df, 'timestamp': time.time()}
                return df
            else:
                logger.error("Processed Tiingo data is empty or missing required columns")
        except Exception as e:
            logger.error(f"Error fetching from Tiingo: {str(e)}")
    else:
        logger.warning("Tiingo API key not found")

    # Fallback to Alpha Vantage
    if api_keys['alpha_vantage']:
        logger.info("Attempting to fetch from Alpha Vantage API with retry")
        try:
            df = _fetch_alpha_vantage(symbol, api_keys['alpha_vantage'])
            if not df.empty and required_cols.issubset(df.columns):
                cache[cache_key] = {'data': df, 'timestamp': time.time()}
                return df
            else:
                logger.error("Processed Alpha Vantage data is empty or missing required columns")
        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {str(e)}")
    else:
        logger.warning("Alpha Vantage API key not found")

    logger.error("Failed to fetch OHLCV data from both sources")
    return None 