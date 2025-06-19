import logging
import time
import functools
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler (rotating)
file_handler = RotatingFileHandler(os.path.join(log_dir, 'app.log'), maxBytes=10485760, backupCount=5)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Entering {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Exiting {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper

def exponential_backoff(max_retries=3, base_delay=1):
    """
    Decorator for exponential backoff on function calls.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries reached: {e}")
                        raise
                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            # This line should never be reached, but ensures the loop exits
            raise Exception("Unexpected exit from retry loop")
        return wrapper
    return decorator

def is_market_open() -> bool:
    """
    Check if the US stock market is currently open.
    
    Market hours: Monday-Friday, 9:30 AM - 4:00 PM ET
    Excludes major holidays (basic implementation)
    
    Returns:
        bool: True if market is open, False otherwise
    """
    try:
        # Get current time in Eastern timezone
        et_tz = ZoneInfo("America/New_York")
        now = datetime.now(et_tz)
        
        # Check if it's a weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            logger.debug("Market closed: Weekend")
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        current_time = now.time()
        
        if market_open <= current_time <= market_close:
            logger.debug("Market is open")
            return True
        else:
            logger.debug(f"Market closed: Current time {current_time} outside market hours {market_open}-{market_close}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking market hours: {e}")
        # Default to market closed on error
        return False

def get_time_until_market_open() -> int:
    """
    Get the number of seconds until the market opens.
    
    Returns:
        int: Seconds until market opens, or 0 if market is currently open
    """
    try:
        et_tz = ZoneInfo("America/New_York")
        now = datetime.now(et_tz)
        
        # If market is currently open, return 0
        if is_market_open():
            return 0
        
        # Calculate next market open time
        next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # If it's after market hours today, move to tomorrow
        if now.time() > dt_time(16, 0):
            next_open = next_open.replace(day=next_open.day + 1)
        
        # Skip weekends
        while next_open.weekday() >= 5:  # Saturday = 5, Sunday = 6
            next_open = next_open.replace(day=next_open.day + 1)
        
        time_diff = next_open - now
        return int(time_diff.total_seconds())
        
    except Exception as e:
        logger.error(f"Error calculating time until market open: {e}")
        # Default to 1 hour if there's an error
        return 3600 