import os
import pandas as pd
import numpy as np
import yfinance as yf
from tiingo import TiingoClient
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from dotenv import load_dotenv
import argparse
import time
import yaml

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, use_tiingo: bool = False, use_alpha_vantage: bool = False):
        """
        Initialize the data collector.
        By default, only use Yahoo Finance to avoid API limits.
        """
        self.use_tiingo = use_tiingo
        self.use_alpha_vantage = use_alpha_vantage
        
        # Load configuration
        config_path = os.path.join('config', 'config.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        if use_tiingo:
            self.tiingo_client = TiingoClient({
                'api_key': os.getenv('TIINGO_API_KEY')
            })
        if use_alpha_vantage:
            self.alpha_vantage = TimeSeries(key=os.getenv('ALPHA_VANTAGE_API_KEY'))
        
        # Use target tickers from config
        self.target_tickers = self.config['data']['target_tickers']
        
    def fetch_yahoo_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from Yahoo Finance with retry logic."""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Use Ticker class for better split handling
                stock = yf.Ticker(ticker)
                data = stock.history(start=start_date, end=end_date, auto_adjust=True)
                
                if data.empty:
                    logger.warning(f"No data returned from Yahoo Finance for {ticker}")
                    return pd.DataFrame()
                
                # Ensure we have all required columns
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                for col in required_cols:
                    if col not in data.columns:
                        data[col] = np.nan
                
                # Select only required columns and rename to standard format
                data = data[required_cols]
                data.columns = [col.lower() for col in required_cols]
                
                return data
            except Exception as e:
                logger.error(f"Error fetching Yahoo data for {ticker} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
        return pd.DataFrame()

    def fetch_tiingo_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from Tiingo with chunking for long periods."""
        if not self.use_tiingo:
            return pd.DataFrame()
            
        try:
            # Split the date range into 1-year chunks to avoid API limitations
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            all_data = []
            current_start = start
            
            while current_start < end:
                current_end = min(current_start + timedelta(days=365), end)
                
                chunk_data = self.tiingo_client.get_dataframe(
                    ticker,
                    startDate=current_start.strftime('%Y-%m-%d'),
                    endDate=current_end.strftime('%Y-%m-%d'),
                    frequency='daily'
                )
                
                if not chunk_data.empty:
                    # Map Tiingo columns to standard format
                    column_mapping = {
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'volume': 'volume'
                    }
                    chunk_data = chunk_data.rename(columns=column_mapping)
                    all_data.append(chunk_data)
                
                current_start = current_end + timedelta(days=1)
                time.sleep(2)  # Increased rate limiting
            
            if not all_data:
                return pd.DataFrame()
                
            return pd.concat(all_data)
        except Exception as e:
            logger.error(f"Error fetching Tiingo data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def fetch_alpha_vantage_data(self, ticker: str) -> pd.DataFrame:
        """Fetch data from Alpha Vantage with retry logic."""
        if not self.use_alpha_vantage:
            return pd.DataFrame()
            
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                data, _ = self.alpha_vantage.get_daily(symbol=ticker, outputsize='full')
                
                # Convert to DataFrame if it's not already
                if isinstance(data, dict):
                    data = pd.DataFrame.from_dict(data, orient='index')
                
                if data.empty:
                    logger.warning(f"No data returned from Alpha Vantage for {ticker}")
                    return pd.DataFrame()
                
                # Map Alpha Vantage columns to standard format
                column_mapping = {
                    '1. open': 'open',
                    '2. high': 'high',
                    '3. low': 'low',
                    '4. close': 'close',
                    '5. volume': 'volume'
                }
                data = data.rename(columns=column_mapping)
                
                return data
            except Exception as e:
                logger.error(f"Error fetching Alpha Vantage data for {ticker} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
        return pd.DataFrame()

    def cross_verify_data(self, yahoo_data: pd.DataFrame, 
                         tiingo_data: pd.DataFrame, 
                         av_data: pd.DataFrame) -> pd.DataFrame:
        """Cross-verify data from different sources and create consensus with OHLCV columns."""
        # Align all dataframes on date index
        dfs = [df for df in [yahoo_data, tiingo_data, av_data] if not df.empty]
        if not dfs:
            return pd.DataFrame()
            
        # Merge all dataframes
        merged = pd.concat(dfs, axis=1)
        
        # Calculate consensus values
        consensus = pd.DataFrame(index=merged.index)
        
        # Consensus for each OHLCV column
        for col in ['open', 'high', 'low', 'close', 'volume']:
            col_candidates = [c for c in merged.columns if col in c]
            if col_candidates:
                # Calculate median instead of mean for more robust consensus
                consensus[col] = merged[col_candidates].median(axis=1)
        
        # Ensure all required columns are present
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in consensus.columns:
                consensus[col] = np.nan
        
        # Sort by date and fill missing values
        consensus = consensus.sort_index()
        
        # Clean and validate the data
        # 1. Remove any negative values
        consensus = consensus.clip(lower=0)
        
        # 2. Ensure High >= Open, High >= Close, Low <= Open, Low <= Close
        consensus['high'] = consensus[['high', 'open', 'close']].max(axis=1)
        consensus['low'] = consensus[['low', 'open', 'close']].min(axis=1)
        
        # 3. Remove any rows where High < Low (shouldn't happen after above fixes)
        consensus = consensus[consensus['high'] >= consensus['low']]
        
        # 4. Fill missing values with forward fill, then backward fill
        consensus = consensus.ffill().bfill()
        
        # 5. Remove any remaining rows with missing values
        consensus = consensus.dropna(subset=required_cols)
        
        # 6. Remove any rows with zero prices
        consensus = consensus[
            (consensus['open'] > 0) & 
            (consensus['high'] > 0) & 
            (consensus['low'] > 0) & 
            (consensus['close'] > 0)
        ]
        
        # 7. Remove any rows with unreasonable price movements (>50% daily change)
        price_changes = consensus['close'].pct_change().abs()
        consensus = consensus[price_changes <= 0.5]
        
        return consensus[required_cols]

    def find_common_date_range(self, historical_data: Dict[str, pd.DataFrame]) -> Tuple[str, str]:
        """Find the common date range where all tickers have data."""
        if not historical_data:
            return None, None
            
        # Get the intersection of all date ranges
        common_start = max(df.index.min() for df in historical_data.values() if not df.empty)
        common_end = min(df.index.max() for df in historical_data.values() if not df.empty)
        
        return common_start.strftime('%Y-%m-%d'), common_end.strftime('%Y-%m-%d')

    def collect_historical_data(self, years: int = None) -> Dict[str, pd.DataFrame]:
        """Collect historical data for all target tickers."""
        if years is None:
            years = self.config['data']['years_of_data']
            
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
        
        historical_data = {}
        for ticker in self.target_tickers:
            logger.info(f"Collecting data for {ticker}")
            
            # Fetch data from all sources
            yahoo_data = self.fetch_yahoo_data(ticker, start_date, end_date)
            tiingo_data = self.fetch_tiingo_data(ticker, start_date, end_date)
            av_data = self.fetch_alpha_vantage_data(ticker)
            
            # Cross-verify and create consensus
            consensus_data = self.cross_verify_data(yahoo_data, tiingo_data, av_data)
            
            if not consensus_data.empty:
                historical_data[ticker] = consensus_data
            else:
                logger.warning(f"No valid data collected for {ticker}")
        
        # Find common date range across all tickers
        if historical_data:
            common_start, common_end = self.find_common_date_range(historical_data)
            logger.info(f"Common date range: {common_start} to {common_end}")
            
            # Align all data to common date range
            for ticker in historical_data:
                historical_data[ticker] = historical_data[ticker].loc[common_start:common_end]
        
        return historical_data

    def load_local_data(self, path: str) -> Dict[str, pd.DataFrame]:
        """Load processed data from local storage."""
        import pickle
        if not os.path.exists(path):
            logger.warning(f"Local data file {path} does not exist.")
            return None
        with open(path, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"Loaded local data from {path}")
        return data

    def save_data(self, data: Dict[str, pd.DataFrame], path: str):
        """Save processed data to local storage."""
        import pickle
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Saved processed data to {path}")

    def get_training_data(self, refresh: bool = False, years: int = None) -> Dict[str, pd.DataFrame]:
        """Load local data if available, otherwise fetch and save new data."""
        local_data_path = os.path.join('data', 'processed', 'training_data.pkl')
        if not refresh and os.path.exists(local_data_path):
            data = self.load_local_data(local_data_path)
            if data:
                return data
        # Otherwise, fetch from APIs
        data = self.collect_historical_data(years=years)
        self.save_data(data, local_data_path)
        return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Collect historical stock data from various sources')
    parser.add_argument('--no-tiingo', action='store_true', help='Disable Tiingo data collection')
    parser.add_argument('--no-alpha-vantage', action='store_true', help='Disable Alpha Vantage data collection')
    args = parser.parse_args()
    
    collector = DataCollector(
        use_tiingo=not args.no_tiingo,
        use_alpha_vantage=not args.no_alpha_vantage
    )
    historical_data = collector.collect_historical_data()
    collector.save_data(historical_data, 'data/processed') 