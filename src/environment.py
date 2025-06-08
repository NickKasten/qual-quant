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
        
        # Validate that all tickers have data
        self.data = {}
        for ticker, df in data.items():
            if df.empty:
                logger.warning(f"No data available for {ticker}, skipping")
                continue
            self.data[ticker] = df
            
        if not self.data:
            raise ValueError("No valid data available for any ticker")
            
        self.tickers = list(self.data.keys())
        if len(self.tickers) < 2:
            raise ValueError("At least 2 tickers with valid data are required")
            
        self.initial_balance = initial_balance
        
        # Verify all dataframes have the same length
        lengths = [len(df) for df in self.data.values()]
        if len(set(lengths)) != 1:
            raise ValueError("All tickers must have the same number of data points")
            
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
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        sma = data['Close'].rolling(window=20).mean()
        std = data['Close'].rolling(window=20).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        return np.column_stack((rsi, macd, (data['Close'] - lower_band) / (upper_band - lower_band)))
        
    def get_observation(self) -> Dict[str, np.ndarray]:
        """Get current state observation."""
        market_data = np.array([
            self._safe_get_ohlcv(self.data[ticker], self.current_step)
            for ticker in self.tickers
        ])
        
        technical_indicators = np.array([
            self._safe_get_technical(self.data[ticker], self.current_step, self.calculate_technical_indicators)
            for ticker in self.tickers
        ])
        
        portfolio_state = np.concatenate([
            self.positions,
            [self.cash]
        ])
        
        # Normalize market data
        # Prices: divide by 1000, Volume: divide by 1e6
        market_data_norm = np.copy(market_data)
        market_data_norm[..., :4] /= 1000.0
        market_data_norm[..., 4] /= 1e6
        
        # Normalize technical indicators (already handled in calculate_technical_indicators, but clamp again)
        tech_norm = np.clip(technical_indicators, -1, 1)
        
        # Normalize portfolio state
        portfolio_state_norm = portfolio_state / max(self.initial_balance, 1.0)
        
        # Clamp all state values to [-10, 10] and replace inf/nan with zeros
        market_data_norm = np.clip(market_data_norm, -10, 10)
        tech_norm = np.clip(tech_norm, -10, 10)
        portfolio_state_norm = np.clip(portfolio_state_norm, -10, 10)
        market_data_norm = np.nan_to_num(market_data_norm, nan=0.0, posinf=0.0, neginf=0.0)
        tech_norm = np.nan_to_num(tech_norm, nan=0.0, posinf=0.0, neginf=0.0)
        portfolio_state_norm = np.nan_to_num(portfolio_state_norm, nan=0.0, posinf=0.0, neginf=0.0)
        
        return {
            'market_data': market_data_norm,
            'technical_indicators': tech_norm,
            'portfolio_state': portfolio_state_norm
        }

    def _safe_get_ohlcv(self, df, step):
        if len(df) == 0:
            return np.zeros(5)
        elif step >= len(df):
            return df.iloc[-1][['Open', 'High', 'Low', 'Close', 'Volume']].values
        else:
            return df.iloc[step][['Open', 'High', 'Low', 'Close', 'Volume']].values

    def _safe_get_technical(self, df, step, calc_func):
        if len(df) == 0:
            return np.zeros(len(calc_func(pd.DataFrame([np.zeros(5)]))))
        elif step >= len(df):
            return calc_func(df)[-1]
        else:
            return calc_func(df.iloc[:step + 1])[-1]
        
    def step(self, action: np.ndarray) -> Tuple[Dict[str, np.ndarray], float, bool, Dict]:
        """Execute one time step within the environment."""
        # Check if next step would be out of bounds
        max_step = len(self.data[self.tickers[0]]) - 1
        if self.current_step >= max_step:
            done = True
            last_valid_step = max_step
            portfolio_value = self.cash + np.sum(self.positions * self.get_current_prices(step=last_valid_step))
            info = {
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'positions': self.positions
            }
            return self.get_observation(), 0.0, done, info

        # Get current prices
        current_prices = self.get_current_prices()
        
        # Calculate total portfolio value
        portfolio_value = self.cash + np.sum(self.positions * current_prices)
        
        # Process each ticker's action
        for i, ticker_action in enumerate(action):
            # Calculate target position value
            target_value = portfolio_value * ticker_action
            
            # Get current position value
            current_value = self.positions[i] * current_prices[i]
            
            # Calculate required change in position
            value_change = target_value - current_value
            
            # Execute the trade
            if value_change > 0:  # Buying
                shares_to_buy = value_change / current_prices[i]
                cost = shares_to_buy * current_prices[i]
                if cost <= self.cash:
                    self.positions[i] += shares_to_buy
                    self.cash -= cost
                else:
                    # If not enough cash, buy what we can
                    shares_to_buy = self.cash / current_prices[i]
                    self.positions[i] += shares_to_buy
                    self.cash = 0
            elif value_change < 0:  # Selling
                shares_to_sell = abs(value_change) / current_prices[i]
                if shares_to_sell <= self.positions[i]:
                    self.positions[i] -= shares_to_sell
                    self.cash += shares_to_sell * current_prices[i]
                else:
                    # If not enough shares, sell what we have
                    self.cash += self.positions[i] * current_prices[i]
                    self.positions[i] = 0
        
        # Move to next time step
        self.current_step += 1
        
        # Calculate new portfolio value
        new_prices = self.get_current_prices()
        new_portfolio_value = self.cash + np.sum(self.positions * new_prices)
        
        # Calculate reward (percentage change in portfolio value)
        reward = (new_portfolio_value - portfolio_value) / portfolio_value
        
        # Scale reward to be more meaningful (multiply by 100 to convert to basis points)
        reward = reward * 100
        
        # Add small penalty for trading to encourage stability
        trading_penalty = -0.01 * np.sum(np.abs(action))
        reward += trading_penalty
        
        # Check if episode is done
        done = self.current_step >= max_step
        
        # Get observation and info
        observation = self.get_observation()
        info = {
            'portfolio_value': new_portfolio_value,
            'cash': self.cash,
            'positions': self.positions,
            'prices': new_prices
        }
        
        return observation, reward, done, info
        
    def reset(self) -> Dict[str, np.ndarray]:
        """Reset the environment to initial state."""
        self.current_step = 0
        self.cash = self.initial_balance
        self.positions = np.zeros(len(self.tickers))
        return self.get_observation()
        
    def get_current_prices(self, step=None) -> np.ndarray:
        """Get current prices for all tickers at the given step (or current_step if None)."""
        if step is None:
            step = self.current_step
        prices = []
        for ticker in self.tickers:
            df = self.data[ticker]
            if len(df) == 0:
                prices.append(0.0)
            elif step >= len(df):
                prices.append(df.iloc[-1]['Close'])
            else:
                prices.append(df.iloc[step]['Close'])
        return np.array(prices)
        
    def render(self, mode='human'):
        """Render the environment."""
        pass  # Implement visualization if needed 