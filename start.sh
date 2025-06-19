#!/bin/bash

export PYTHONPATH="/app"

echo "Checking environment variables..."

if [ -z "$TIINGO_API_KEY" ] || [ -z "$ALPHA_VANTAGE_API_KEY" ] || [ -z "$ALPACA_API_KEY" ] || [ -z "$ALPACA_SECRET_KEY" ] || [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
  echo "Error: Missing required environment variables"
  exit 1
fi

echo "All required environment variables are set"

# Check if we should run API server or trading bot
if [ "$RUN_MODE" = "api" ]; then
    echo "Starting API server..."
    exec python -m backend.app.api_server
else
    echo "Starting trading bot..."
    exec python -m backend.app.main
fi 