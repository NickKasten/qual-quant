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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.tiingo_client = TiingoClient({
            'api_key': os.getenv('TIINGO_API_KEY')
        })
        self.alpha_vantage = TimeSeries(key=os.getenv('ALPHA_VANTAGE_API_KEY'))
        
        # Top 5 Dow Jones stocks by market cap
        self.target_tickers = ['AAPL', 'MSFT', 'JPM', 'V', 'WMT']
        
    def fetch_yahoo_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from Yahoo Finance."""
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            data.columns = [f'yahoo_{col.lower()}' for col in data.columns]
            return data
        except Exception as e:
            logger.error(f"Error fetching Yahoo data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def fetch_tiingo_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from Tiingo."""
        try:
            data = self.tiingo_client.get_dataframe(
                ticker,
                startDate=start_date,
                endDate=end_date,
                frequency='daily'
            )
            data.columns = [f'tiingo_{col.lower()}' for col in data.columns]
            return data
        except Exception as e:
            logger.error(f"Error fetching Tiingo data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def fetch_alpha_vantage_data(self, ticker: str) -> pd.DataFrame:
        """Fetch data from Alpha Vantage."""
        try:
            data, _ = self.alpha_vantage.get_daily(symbol=ticker, outputsize='full')
            data.columns = [f'av_{col.lower()}' for col in data.columns]
            return data
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def cross_verify_data(self, yahoo_data: pd.DataFrame, 
                         tiingo_data: pd.DataFrame, 
                         av_data: pd.DataFrame) -> pd.DataFrame:
        """Cross-verify data from different sources and create consensus."""
        # Align all dataframes on date index
        dfs = [df for df in [yahoo_data, tiingo_data, av_data] if not df.empty]
        if not dfs:
            return pd.DataFrame()
            
        # Merge all dataframes
        merged = pd.concat(dfs, axis=1)
        
        # Calculate consensus values
        consensus = pd.DataFrame()
        
        # Price consensus (weighted average)
        price_cols = [col for col in merged.columns if 'close' in col]
        if price_cols:
            consensus['close'] = merged[price_cols].mean(axis=1)
            
        # Volume consensus
        volume_cols = [col for col in merged.columns if 'volume' in col]
        if volume_cols:
            consensus['volume'] = merged[volume_cols].mean(axis=1)
            
        # High/Low consensus
        high_cols = [col for col in merged.columns if 'high' in col]
        low_cols = [col for col in merged.columns if 'low' in col]
        if high_cols:
            consensus['high'] = merged[high_cols].mean(axis=1)
        if low_cols:
            consensus['low'] = merged[low_cols].mean(axis=1)
            
        return consensus

    def collect_historical_data(self, years: int = 30) -> Dict[str, pd.DataFrame]:
        """Collect and cross-verify historical data for all target tickers."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        historical_data = {}
        
        for ticker in self.target_tickers:
            logger.info(f"Collecting data for {ticker}")
            
            # Fetch data from all sources
            yahoo_data = self.fetch_yahoo_data(ticker, start_date_str, end_date_str)
            tiingo_data = self.fetch_tiingo_data(ticker, start_date_str, end_date_str)
            av_data = self.fetch_alpha_vantage_data(ticker)
            
            # Cross-verify and create consensus
            consensus_data = self.cross_verify_data(yahoo_data, tiingo_data, av_data)
            
            if not consensus_data.empty:
                historical_data[ticker] = consensus_data
                
        return historical_data

    def save_data(self, data: Dict[str, pd.DataFrame], path: str):
        """Save collected data to disk."""
        os.makedirs(path, exist_ok=True)
        for ticker, df in data.items():
            df.to_csv(os.path.join(path, f'{ticker}_historical.csv'))

if __name__ == "__main__":
    collector = DataCollector()
    historical_data = collector.collect_historical_data()
    collector.save_data(historical_data, 'data/processed') 