import os

class ConfigError(Exception):
    pass

REQUIRED_ENV_VARS = [
    "TIIINGO_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY"
]

def load_config():
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")
    return {
        "TIIINGO_API_KEY": os.getenv("TIIINGO_API_KEY"),
        "ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY"),
        "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY"),
        "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "TIIINGO_BASE_URL": "https://api.tiingo.com/tiingo/daily",
        "ALPHA_VANTAGE_BASE_URL": "https://www.alphavantage.co/query",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets"
    }

def get_public_config():
    """
    Return config values safe for logging (excludes secrets).
    """
    cfg = load_config()
    return {
        "SUPABASE_URL": cfg["SUPABASE_URL"],
        "TIIINGO_BASE_URL": cfg["TIIINGO_BASE_URL"],
        "ALPHA_VANTAGE_BASE_URL": cfg["ALPHA_VANTAGE_BASE_URL"],
        "ALPACA_BASE_URL": cfg["ALPACA_BASE_URL"]
    } 