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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, use_tiingo: bool = True, use_alpha_vantage: bool = True):
        self.use_tiingo = use_tiingo
        self.use_alpha_vantage = use_alpha_vantage
        
        if use_tiingo:
            self.tiingo_client = TiingoClient({
                'api_key': os.getenv('TIINGO_API_KEY')
            })
        if use_alpha_vantage:
            self.alpha_vantage = TimeSeries(key=os.getenv('ALPHA_VANTAGE_API_KEY'))
        
        # Top 5 Dow Jones stocks by market cap
        self.target_tickers = ['AAPL', 'MSFT', 'JPM', 'V', 'WMT']
        
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
                
                # Fix column renaming for MultiIndex columns
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [f'yahoo_{col[0].lower()}' for col in data.columns]
                else:
                    data.columns = [f'yahoo_{col.lower()}' for col in data.columns]
                return data
            except Exception as e:
                logger.error(f"Error fetching Yahoo data for {ticker} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
        return pd.DataFrame()

    def fetch_tiingo_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from Tiingo with chunking for long periods."""
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
                    chunk_data.columns = [f'tiingo_{col.lower()}' for col in chunk_data.columns]
                    all_data.append(chunk_data)
                
                current_start = current_end + timedelta(days=1)
                time.sleep(1)  # Rate limiting
            
            if not all_data:
                return pd.DataFrame()
                
            return pd.concat(all_data)
        except Exception as e:
            logger.error(f"Error fetching Tiingo data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def fetch_alpha_vantage_data(self, ticker: str) -> pd.DataFrame:
        """Fetch data from Alpha Vantage with retry logic."""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                data, _ = self.alpha_vantage.get_daily(symbol=ticker, outputsize='full')
                if data.empty:
                    logger.warning(f"No data returned from Alpha Vantage for {ticker}")
                    return pd.DataFrame()
                    
                data.columns = [f'av_{col.lower()}' for col in data.columns]
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
                consensus[col.capitalize()] = merged[col_candidates].median(axis=1)
        
        # Ensure all required columns are present
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in consensus.columns:
                consensus[col] = np.nan
        
        # Sort by date and fill missing values
        consensus = consensus.sort_index()
        
        # Clean and validate the data
        # 1. Remove any negative values
        consensus = consensus.clip(lower=0)
        
        # 2. Ensure High >= Open, High >= Close, Low <= Open, Low <= Close
        consensus['High'] = consensus[['High', 'Open', 'Close']].max(axis=1)
        consensus['Low'] = consensus[['Low', 'Open', 'Close']].min(axis=1)
        
        # 3. Remove any rows where High < Low (shouldn't happen after above fixes)
        consensus = consensus[consensus['High'] >= consensus['Low']]
        
        # 4. Fill missing values with forward fill, then backward fill
        consensus = consensus.fillna(method='ffill').fillna(method='bfill')
        
        # 5. Remove any remaining rows with missing values
        consensus = consensus.dropna(subset=required_cols)
        
        # 6. Remove any rows with zero prices
        consensus = consensus[
            (consensus['Open'] > 0) & 
            (consensus['High'] > 0) & 
            (consensus['Low'] > 0) & 
            (consensus['Close'] > 0)
        ]
        
        # 7. Remove any rows with unreasonable price movements (>50% daily change)
        price_changes = consensus['Close'].pct_change().abs()
        consensus = consensus[price_changes <= 0.5]
        
        # 8. For AAPL, keep both regular market hours and after-hours data
        # This is done by not resampling or aggregating the data
        # The dual timestamps will be preserved in the output
        
        return consensus[required_cols]

    def find_common_date_range(self, historical_data: Dict[str, pd.DataFrame]) -> Tuple[str, str]:
        """Find the common date range where all tickers have data."""
        if not historical_data:
            return None, None
            
        # Get the intersection of all date ranges
        common_start = max(df.index.min() for df in historical_data.values() if not df.empty)
        common_end = min(df.index.max() for df in historical_data.values() if not df.empty)
        
        return common_start.strftime('%Y-%m-%d'), common_end.strftime('%Y-%m-%d')

    def collect_historical_data(self, years: int = 30) -> Dict[str, pd.DataFrame]:
        """Collect and cross-verify historical data for all target tickers."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        historical_data = {}
        
        for ticker in self.target_tickers:
            logger.info(f"Collecting data for {ticker}")
            
            # Fetch data from enabled sources
            yahoo_data = self.fetch_yahoo_data(ticker, start_date_str, end_date_str)
            tiingo_data = pd.DataFrame() if not self.use_tiingo else self.fetch_tiingo_data(ticker, start_date_str, end_date_str)
            av_data = pd.DataFrame() if not self.use_alpha_vantage else self.fetch_alpha_vantage_data(ticker)
            
            # Cross-verify and create consensus
            consensus_data = self.cross_verify_data(yahoo_data, tiingo_data, av_data)
            historical_data[ticker] = consensus_data
        
        # Find common date range where all tickers have data
        common_start, common_end = self.find_common_date_range(historical_data)
        if common_start and common_end:
            logger.info(f"Common date range: {common_start} to {common_end}")
            # Filter data to only include the common date range
            for ticker in self.target_tickers:
                historical_data[ticker] = historical_data[ticker][common_start:common_end]
                
            # Verify all dataframes have the same length
            lengths = [len(df) for df in historical_data.values()]
            if len(set(lengths)) != 1:
                logger.warning(f"Data lengths after filtering: {dict(zip(self.target_tickers, lengths))}")
                # Find the shortest length and trim all dataframes to that length
                min_length = min(lengths)
                for ticker in self.target_tickers:
                    historical_data[ticker] = historical_data[ticker].iloc[-min_length:]
                logger.info(f"Trimmed all dataframes to {min_length} points")
        else:
            logger.warning("No common date range found for all tickers")
            
        return historical_data

    def save_data(self, data: Dict[str, pd.DataFrame], path: str):
        """Save collected data to disk."""
        os.makedirs(path, exist_ok=True)
        for ticker, df in data.items():
            df.to_csv(os.path.join(path, f'{ticker}_historical.csv'))
            logger.info(f"Saved {len(df)} days of data for {ticker}")

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