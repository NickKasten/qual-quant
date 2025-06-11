import logging
import time
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def exponential_backoff(max_retries=3, base_delay=1):
    """
    Decorator for exponential backoff on function calls.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries reached: {e}")
                        raise
                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        return wrapper
    return decorator 