import os
import logging
import requests
import time
import pandas as pd
from typing import Optional
import tenacity

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logging.warning("yfinance not available, skipping as fallback option")

logger = logging.getLogger(__name__)

TIINGO_BASE_URL = "https://api.tiingo.com/tiingo/daily"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Enhanced in-memory cache with fallback support
cache = {}
fallback_cache = {}  # Long-term cache for emergency fallback
CACHE_TTL = 300  # 5 minutes
FALLBACK_CACHE_TTL = 86400  # 24 hours

def _get_api_keys():
    """Get API keys from environment variables, including rotation support."""
    alpha_vantage_keys = []
    
    # Primary Alpha Vantage key
    primary_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if primary_key:
        alpha_vantage_keys.append(primary_key)
    
    # Additional Alpha Vantage keys for rotation (ALPHA_VANTAGE_API_KEY_2, etc.)
    for i in range(2, 6):  # Support up to 5 keys
        key = os.getenv(f"ALPHA_VANTAGE_API_KEY_{i}")
        if key:
            alpha_vantage_keys.append(key)
    
    return {
        'tiingo': os.getenv("TIINGO_API_KEY"),
        'alpha_vantage_keys': alpha_vantage_keys
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

class RateLimitError(Exception):
    """Custom exception for rate limit errors."""
    pass

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type((requests.RequestException, Exception)) & tenacity.retry_if_not_exception_type(RateLimitError),
    reraise=True,
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
)
def _fetch_tiingo(symbol, api_key):
    # Calculate date range for historical data (120 days to ensure we have 80+ trading days)
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
    
    response = requests.get(
        f"{TIINGO_BASE_URL}/{symbol}/prices",
        params={
            "token": api_key, 
            "format": "json",
            "startDate": start_date,
            "endDate": end_date
        }
    )
    logger.info(f"Tiingo API response status: {response.status_code}")
    
    # Check for rate limit (429) or quota exceeded (403)
    if response.status_code in [429, 403]:
        error_msg = f"Tiingo rate limit/quota exceeded (status: {response.status_code})"
        logger.warning(error_msg)
        raise RateLimitError(error_msg)
    
    if response.status_code == 200:
        data = response.json()
        # Check if response indicates rate limit in the data
        if isinstance(data, dict) and ('error' in data or 'Error' in data):
            error_text = data.get('error', data.get('Error', ''))
            if 'rate limit' in error_text.lower() or 'quota' in error_text.lower():
                logger.warning(f"Tiingo rate limit in response: {error_text}")
                raise RateLimitError(f"Tiingo rate limit: {error_text}")
        
        df = _process_tiingo_data(data)
        return df
    else:
        logger.error(f"Tiingo API error: {response.text}")
        raise Exception(f"Tiingo API error (status: {response.status_code})")

def _fetch_alpha_vantage_with_key(symbol, api_key):
    """Fetch data from Alpha Vantage with a single key."""
    response = requests.get(
        ALPHA_VANTAGE_BASE_URL,
        params={
            "function": "TIME_SERIES_DAILY", 
            "symbol": symbol, 
            "apikey": api_key,
            "outputsize": "full"  # Gets more historical data instead of just last 100 days
        }
    )
    logger.info(f"Alpha Vantage API response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'Error Message' in data:
            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
            raise Exception("Alpha Vantage API error")
        # Check for rate limit messages
        if 'Note' in data and 'rate limit' in data['Note'].lower():
            logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            raise RateLimitError(f"Alpha Vantage rate limit: {data['Note']}")
        df = _process_alpha_vantage_data(data)
        return df
    else:
        logger.error(f"Alpha Vantage API error: {response.text}")
        raise Exception(f"Alpha Vantage API error (status: {response.status_code})")

def _fetch_alpha_vantage(symbol, api_keys):
    """Fetch data from Alpha Vantage with key rotation."""
    if not api_keys:
        raise Exception("No Alpha Vantage API keys available")
    
    for i, api_key in enumerate(api_keys):
        try:
            logger.info(f"Trying Alpha Vantage key #{i+1}")
            return _fetch_alpha_vantage_with_key(symbol, api_key)
        except RateLimitError as e:
            logger.warning(f"Alpha Vantage key #{i+1} hit rate limit: {str(e)}")
            if i == len(api_keys) - 1:  # Last key
                raise e
            logger.info(f"Rotating to next Alpha Vantage key...")
            continue
        except Exception as e:
            logger.error(f"Alpha Vantage key #{i+1} failed: {str(e)}")
            if i == len(api_keys) - 1:  # Last key
                raise e
            continue
    
    raise Exception("All Alpha Vantage keys failed")

def _fetch_yfinance(symbol):
    """Fetch data from yfinance as a last resort fallback."""
    if not YFINANCE_AVAILABLE:
        raise Exception("yfinance not available")
    
    logger.info("Fetching data from yfinance")
    
    # Get 6 months of data to ensure sufficient history
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo")
    
    if df.empty:
        raise Exception("yfinance returned empty data")
    
    # Rename columns to match expected format
    df.columns = df.columns.str.lower()
    
    # Ensure we have the required columns
    required_cols = {'open', 'high', 'low', 'close', 'volume'}
    if not required_cols.issubset(df.columns):
        raise Exception(f"yfinance data missing required columns: {required_cols - set(df.columns)}")
    
    logger.info(f"yfinance data shape: {df.shape}")
    return df

def fetch_ohlcv(symbol: str = "AAPL") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data with multiple fallbacks and caching.
    
    Data sources (in order):
    1. Tiingo API (primary - most reliable)
    2. Alpha Vantage API (fallback with key rotation)
    3. yfinance (last resort - free but less reliable)
    
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
        logger.info("🔹 Attempting to fetch from Tiingo API (primary source)")
        try:
            df = _fetch_tiingo(symbol, api_keys['tiingo'])
            if not df.empty and required_cols.issubset(df.columns):
                logger.info(f"✅ Successfully fetched from Tiingo - data shape: {df.shape}")
                # Update both regular cache and fallback cache
                cache[cache_key] = {'data': df, 'timestamp': time.time()}
                fallback_cache[cache_key] = {'data': df, 'timestamp': time.time()}
                return df
            else:
                logger.error("❌ Processed Tiingo data is empty or missing required columns")
        except RateLimitError as e:
            logger.warning(f"⚠️  Tiingo rate limit hit: {str(e)}")
            logger.info("🔄 Falling back to Alpha Vantage due to rate limit")
        except Exception as e:
            logger.error(f"❌ Error fetching from Tiingo: {str(e)}")
            logger.info("🔄 Falling back to Alpha Vantage due to error")
    else:
        logger.warning("⚠️  Tiingo API key not found, using Alpha Vantage")

    # Fallback to Alpha Vantage with key rotation
    if api_keys['alpha_vantage_keys']:
        logger.info(f"🔸 Attempting to fetch from Alpha Vantage API (fallback source) with {len(api_keys['alpha_vantage_keys'])} keys")
        try:
            df = _fetch_alpha_vantage(symbol, api_keys['alpha_vantage_keys'])
            if not df.empty and required_cols.issubset(df.columns):
                logger.info(f"✅ Successfully fetched from Alpha Vantage - data shape: {df.shape}")
                # Update both regular cache and fallback cache
                cache[cache_key] = {'data': df, 'timestamp': time.time()}
                fallback_cache[cache_key] = {'data': df, 'timestamp': time.time()}
                return df
            else:
                logger.error("❌ Processed Alpha Vantage data is empty or missing required columns")
        except Exception as e:
            logger.error(f"❌ Error fetching from Alpha Vantage: {str(e)}")
    else:
        logger.warning("⚠️  No Alpha Vantage API keys found")

    # Last resort: yfinance
    if YFINANCE_AVAILABLE:
        logger.info("🔺 Attempting to fetch from yfinance (last resort)")
        try:
            df = _fetch_yfinance(symbol)
            if not df.empty and required_cols.issubset(df.columns):
                logger.info(f"✅ Successfully fetched from yfinance - data shape: {df.shape}")
                # Update both regular cache and fallback cache
                cache[cache_key] = {'data': df, 'timestamp': time.time()}
                fallback_cache[cache_key] = {'data': df, 'timestamp': time.time()}
                return df
            else:
                logger.error("❌ Processed yfinance data is empty or missing required columns")
        except Exception as e:
            logger.error(f"❌ Error fetching from yfinance: {str(e)}")
    else:
        logger.warning("⚠️  yfinance not available")

    # Final fallback: use cached data if available (even if stale)
    if cache_key in fallback_cache:
        age_hours = (time.time() - fallback_cache[cache_key]['timestamp']) / 3600
        if age_hours < 24:  # Use cache if less than 24 hours old
            logger.warning(f"🔄 Using stale cached data from {age_hours:.1f} hours ago")
            return fallback_cache[cache_key]['data']
        else:
            logger.warning(f"🗑️  Cached data too old ({age_hours:.1f} hours), discarding")

    # Graceful skip instead of error
    logger.warning("⏭️  GRACEFUL SKIP: All data sources unavailable, trading cycle will be skipped")
    return None 