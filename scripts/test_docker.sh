#!/bin/bash

# Exit on error
set -e

echo "Building Docker container..."
docker compose build

echo "Testing container environment variables..."
docker compose run --rm trading-bot python -c "
import os
required_vars = [
    'TIINGO_API_KEY',
    'ALPHA_VANTAGE_API_KEY',
    'ALPACA_API_KEY',
    'ALPACA_SECRET_KEY',
    'SUPABASE_URL',
    'SUPABASE_KEY'
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f'Missing environment variables: {missing_vars}')
    exit(1)
print('All environment variables are set')
"

echo "Testing container logging..."
docker compose run --rm trading-bot python -c "
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Test log message')
"

echo "Testing external service connections..."
docker compose run --rm trading-bot python -c "
from data.fetcher import fetch_ohlcv
from broker.paper import PaperBroker
from db.supabase import SupabaseDB

# Test data fetching
print('Testing data fetching...')
data = fetch_ohlcv('AAPL', '1d', '1y')
print(f'Successfully fetched data for AAPL: {len(data)} rows')

# Test broker connection
print('Testing broker connection...')
broker = PaperBroker()
print('Successfully initialized broker')

# Test database connection
print('Testing database connection...')
db = SupabaseDB()
print('Successfully initialized database connection')
"

echo "All tests completed successfully!" 