import unittest
import os
import time
from dotenv import load_dotenv
from data.fetcher import fetch_ohlcv, cache, CACHE_TTL

# Load environment variables from .env file
load_dotenv()

class TestDataFetcher(unittest.TestCase):
    def setUp(self):
        # Ensure environment variables are set
        self.tiingo_key = os.getenv("TIIINGO_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.tiingo_key or not self.alpha_vantage_key:
            self.skipTest("API keys not set in environment variables")

    def test_cache_hit(self):
        # Test cache hit
        symbol = "AAPL"
        fetch_ohlcv(symbol)
        self.assertIn(f"{symbol}_ohlcv", cache)
        self.assertLess(time.time() - cache[f"{symbol}_ohlcv"]['timestamp'], CACHE_TTL)

    def test_cache_miss(self):
        # Test cache miss
        symbol = "MSFT"
        fetch_ohlcv(symbol)
        self.assertIn(f"{symbol}_ohlcv", cache)

    def test_error_handling(self):
        # Test error handling
        os.environ["TIIINGO_API_KEY"] = "invalid_key"
        result = fetch_ohlcv("AAPL")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main() 