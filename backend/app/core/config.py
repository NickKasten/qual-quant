import os

class ConfigError(Exception):
    pass

REQUIRED_ENV_VARS = [
    "TIINGO_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY"
]

LEGAL_DISCLAIMER = (
    "This service is for informational and educational purposes only. "
    "Nothing herein should be construed as financial advice, a solicitation, or a recommendation to buy or sell any security. "
    "Trading involves risk and you may lose money. Please consult a qualified financial advisor before making investment decisions."
)

def load_config():
    # Check TEST_MODE at function call time, not import time
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    if not test_mode:
        missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing:
            raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")
    
    return {
        "TIINGO_API_KEY": os.getenv("TIINGO_API_KEY", "test_key"),
        "ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY", "test_key"),
        "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", "test_key"),
        "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", "test_key"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL", "https://test.supabase.co"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY", "test_key"),
        "TIINGO_BASE_URL": "https://api.tiingo.com/tiingo/daily",
        "ALPHA_VANTAGE_BASE_URL": "https://www.alphavantage.co/query",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "TEST_MODE": test_mode,
        "STARTING_EQUITY": os.getenv("STARTING_EQUITY", "100000")
    }

def get_public_config():
    """
    Return config values safe for logging (excludes secrets).
    """
    cfg = load_config()
    return {
        "SUPABASE_URL": cfg["SUPABASE_URL"],
        "TIINGO_BASE_URL": cfg["TIINGO_BASE_URL"],
        "ALPHA_VANTAGE_BASE_URL": cfg["ALPHA_VANTAGE_BASE_URL"],
        "ALPACA_BASE_URL": cfg["ALPACA_BASE_URL"],
        "TEST_MODE": cfg["TEST_MODE"]
    } 