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
import sys
sys.path.append('/app')
from backend.app.services.fetcher import fetch_ohlcv
from backend.app.services.broker.paper import execute_trade
from backend.app.db.supabase import get_supabase_client

# Test data fetching
print('Testing data fetching...')
data = fetch_ohlcv('AAPL')
print(f'Successfully fetched data for AAPL: {len(data)} rows')

# Test broker connection
print('Testing broker connection...')
trade = execute_trade(10, symbol='AAPL', side='buy', simulate=True)
print('Successfully executed simulated trade')

# Test database connection
print('Testing database connection...')
db = get_supabase_client()
print('Successfully initialized database connection')
"

echo "All tests completed successfully!" 