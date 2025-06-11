import os

# API Keys
TIIINGO_API_KEY = os.getenv("TIIINGO_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Constants
TIIINGO_BASE_URL = "https://api.tiingo.com/tiingo/daily"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets" 