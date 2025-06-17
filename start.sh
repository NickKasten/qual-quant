#!/bin/bash

echo "Checking environment variables..."

if [ -z "$TIINGO_API_KEY" ] || [ -z "$ALPHA_VANTAGE_API_KEY" ] || [ -z "$ALPACA_API_KEY" ] || [ -z "$ALPACA_SECRET_KEY" ] || [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
  echo "Error: Missing required environment variables"
  exit 1
fi

echo "All required environment variables are set"

exec python backend/app/main.py 