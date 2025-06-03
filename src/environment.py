import gym
import numpy as np
import pandas as pd
from gym import spaces
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class TradingEnvironment(gym.Env):
    def __init__(self, data: Dict[str, pd.DataFrame], initial_balance: float = 100000.0):
        super(TradingEnvironment, self).__init__()
        
        self.data = data
        self.tickers = list(data.keys())
        self.initial_balance = initial_balance
        
        # Define action space (continuous actions for each ticker)
        # Actions represent the fraction of portfolio to allocate to each ticker
        self.action_space = spaces.Box(
            low=-1.0,  # Short selling allowed
            high=1.0,  # Maximum long position
            shape=(len(self.tickers),),
            dtype=np.float32
        )
        
        # Define observation space
        # Features: OHLCV data, technical indicators, portfolio state
        self.observation_space = spaces.Dict({
            'market_data': spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(len(self.tickers), 5),  # OHLCV
                dtype=np.float32
            ),
            'technical_indicators': spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(len(self.tickers), 3),  # RSI, MACD, Bollinger Bands
                dtype=np.float32
            ),
            'portfolio_state': spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(len(self.tickers) + 1,),  # Positions + cash
                dtype=np.float32
            )
        })
        
        self.reset()
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> np.ndarray:
        """Calculate technical indicators for a given ticker."""
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = data['close'].ewm(span=12, adjust=False).mean()
        exp2 = data['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        sma = data['close'].rolling(window=20).mean()
        std = data['close'].rolling(window=20).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        return np.column_stack((rsi, macd, (data['close'] - lower_band) / (upper_band - lower_band)))
        
    def get_observation(self) -> Dict[str, np.ndarray]:
        """Get current state observation."""
        market_data = np.array([
            self.data[ticker].iloc[self.current_step][['open', 'high', 'low', 'close', 'volume']].values
            for ticker in self.tickers
        ])
        
        technical_indicators = np.array([
            self.calculate_technical_indicators(self.data[ticker].iloc[:self.current_step + 1])[-1]
            for ticker in self.tickers
        ])
        
        portfolio_state = np.concatenate([
            self.positions,
            [self.cash]
        ])
        
        return {
            'market_data': market_data,
            'technical_indicators': technical_indicators,
            'portfolio_state': portfolio_state
        }
        
    def step(self, action: np.ndarray) -> Tuple[Dict[str, np.ndarray], float, bool, Dict]:
        """Execute one time step within the environment."""
        self.current_step += 1
        
        # Normalize actions to sum to 1
        action = action / np.sum(np.abs(action))
        
        # Calculate new positions
        portfolio_value = self.cash + np.sum(self.positions * self.get_current_prices())
        target_positions = action * portfolio_value
        position_changes = target_positions - self.positions
        
        # Update positions and cash
        self.positions += position_changes
        self.cash -= np.sum(position_changes * self.get_current_prices())
        
        # Calculate reward (portfolio return)
        new_portfolio_value = self.cash + np.sum(self.positions * self.get_current_prices())
        reward = (new_portfolio_value - portfolio_value) / portfolio_value
        
        # Check if episode is done
        done = self.current_step >= len(self.data[self.tickers[0]]) - 1
        
        info = {
            'portfolio_value': new_portfolio_value,
            'cash': self.cash,
            'positions': self.positions
        }
        
        return self.get_observation(), reward, done, info
        
    def reset(self) -> Dict[str, np.ndarray]:
        """Reset the environment to initial state."""
        self.current_step = 0
        self.cash = self.initial_balance
        self.positions = np.zeros(len(self.tickers))
        return self.get_observation()
        
    def get_current_prices(self) -> np.ndarray:
        """Get current prices for all tickers."""
        return np.array([
            self.data[ticker].iloc[self.current_step]['close']
            for ticker in self.tickers
        ])
        
    def render(self, mode='human'):
        """Render the environment."""
        pass  # Implement visualization if needed 