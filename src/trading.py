import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import torch

from data_collection import DataCollector
from environment import TradingEnvironment
from sac_agent import SACAgent
from llm_validator import LLMValidator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingSystem:
    def __init__(self,
                 initial_balance: float = 100000.0,
                 train_episodes: int = 1000,
                 eval_episodes: int = 100,
                 batch_size: int = 64,
                 buffer_size: int = 1000000,
                 use_llm: bool = False):
        
        self.initial_balance = initial_balance
        self.train_episodes = train_episodes
        self.eval_episodes = eval_episodes
        self.batch_size = batch_size
        self.buffer_size = buffer_size
        self.use_llm = use_llm
        
        # Initialize components
        self.data_collector = DataCollector()
        if self.use_llm:
            self.llm_validator = LLMValidator()
        
        # Load or collect data
        self.market_data = self._load_or_collect_data()
        
        # Validate data before proceeding
        self._validate_data()
        
        # Initialize environment
        self.env = TradingEnvironment(self.market_data, initial_balance)
        
        # Initialize SAC agent
        self.agent = SACAgent(
            state_dim=self.env.observation_space.spaces,
            action_dim=self.env.action_space.shape[0]
        )
        
        # Initialize replay buffer
        self.replay_buffer = []
        
    def _validate_data(self):
        """Validate the loaded market data for completeness and correctness."""
        logger.info("Validating market data...")
        
        if not self.market_data:
            raise ValueError("No market data loaded")
            
        # Check for required tickers
        required_tickers = ['AAPL', 'MSFT', 'JPM', 'V', 'WMT']  # Top 5 Dow Jones tickers
        missing_tickers = [ticker for ticker in required_tickers if ticker not in self.market_data]
        if missing_tickers:
            raise ValueError(f"Missing data for required tickers: {missing_tickers}")
            
        # Validate each ticker's data
        for ticker, data in self.market_data.items():
            # Check for required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise ValueError(f"Missing columns for {ticker}: {missing_columns}")
                
            # Check for missing values
            missing_values = data[required_columns].isnull().sum()
            if missing_values.any():
                raise ValueError(f"Found missing values in {ticker} data:\n{missing_values}")
                
            # Check for negative values
            negative_values = (data[required_columns] < 0).any()
            if negative_values.any():
                raise ValueError(f"Found negative values in {ticker} data")
                
            # Check for zero or infinite values
            zero_values = (data[required_columns] == 0).any()
            inf_values = np.isinf(data[required_columns]).any()
            if zero_values.any() or inf_values.any():
                logger.warning(f"Found zero or infinite values in {ticker} data")
                
            # Check date range
            date_range = data.index.max() - data.index.min()
            if date_range.days < 365 * 30:  # 30 years of data
                logger.warning(f"{ticker} data spans less than 30 years: {date_range.days} days")
                
            # Check for duplicate dates
            if data.index.duplicated().any():
                raise ValueError(f"Found duplicate dates in {ticker} data")
                
            # Check for data consistency
            price_consistency = (data['High'] >= data['Low']).all() and \
                              (data['High'] >= data['Open']).all() and \
                              (data['High'] >= data['Close']).all() and \
                              (data['Low'] <= data['Open']).all() and \
                              (data['Low'] <= data['Close']).all()
            if not price_consistency:
                raise ValueError(f"Found inconsistent price data in {ticker}")
                
            # Check for reasonable price ranges
            price_stats = data[['Open', 'High', 'Low', 'Close']].describe()
            if (price_stats.loc['max'] > 1000000).any() or (price_stats.loc['min'] < 0).any():
                logger.warning(f"Unusual price ranges detected in {ticker} data")
                
            # Check for reasonable volume ranges
            volume_stats = data['Volume'].describe()
            if volume_stats.loc['max'] > 1e12 or volume_stats.loc['min'] < 0:
                logger.warning(f"Unusual volume ranges detected in {ticker} data")
        
        logger.info("Market data validation completed successfully")
        
    def _load_or_collect_data(self) -> Dict[str, pd.DataFrame]:
        """Load existing data or collect new data."""
        data_path = "data/processed"
        
        if os.path.exists(data_path):
            logger.info("Loading existing data...")
            market_data = {}
            for file in os.listdir(data_path):
                if file.endswith("_historical.csv"):
                    ticker = file.split("_")[0]
                    try:
                        market_data[ticker] = pd.read_csv(
                            os.path.join(data_path, file),
                            index_col=0,
                            parse_dates=True
                        )
                        logger.info(f"Successfully loaded data for {ticker}")
                    except Exception as e:
                        logger.error(f"Error loading data for {ticker}: {str(e)}")
                        raise
            return market_data
        else:
            logger.info("Collecting new data...")
            return self.data_collector.collect_historical_data()
            
    def train(self):
        """Train the SAC agent without LLM validation."""
        logger.info("Starting SAC training...")
        
        for episode in range(self.train_episodes):
            state = self.env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                # Get SAC decision
                action = self.agent.select_action(state)
                
                # Execute action directly (no LLM validation during training)
                next_state, reward, done, info = self.env.step(action)
                
                # Store transition in replay buffer
                self.replay_buffer.append({
                    'state': state,
                    'action': action,
                    'reward': reward,
                    'next_state': next_state,
                    'done': done
                })
                
                # Maintain buffer size
                if len(self.replay_buffer) > self.buffer_size:
                    self.replay_buffer.pop(0)
                
                # Update agent if enough samples
                if len(self.replay_buffer) >= self.batch_size:
                    batch = self._sample_batch()
                    losses = self.agent.update(batch)
                    
                    if episode % 10 == 0:
                        logger.info(f"Episode {episode}, Losses: {losses}")
                
                state = next_state
                episode_reward += reward
            
            if episode % 10 == 0:
                logger.info(f"Episode {episode}, Total Reward: {episode_reward}")
                
    def evaluate(self, use_llm: bool = None) -> Dict[str, float]:
        """Evaluate the trained agent with optional LLM validation."""
        if use_llm is None:
            use_llm = self.use_llm
            
        logger.info(f"Starting evaluation with LLM validation: {use_llm}")
        
        total_rewards = []
        portfolio_values = []
        sac_rewards = []  # Track rewards without LLM validation
        
        for episode in range(self.eval_episodes):
            state = self.env.reset()
            episode_reward = 0
            sac_episode_reward = 0
            done = False
            
            while not done:
                # Get SAC decision
                action = self.agent.select_action(state, evaluate=True)
                
                if use_llm:
                    # Get LLM validation
                    validated_action = self.llm_validator.validate_decision(
                        action,
                        self.env.tickers,
                        self.env.data[self.env.tickers[0]].index[self.env.current_step],
                        self.market_data
                    )
                    
                    # Execute validated action
                    next_state, reward, done, info = self.env.step(validated_action)
                else:
                    # Execute SAC action directly
                    next_state, reward, done, info = self.env.step(action)
                
                state = next_state
                episode_reward += reward
                
                if done:
                    portfolio_values.append(info['portfolio_value'])
            
            total_rewards.append(episode_reward)
            
        return {
            'mean_reward': np.mean(total_rewards),
            'std_reward': np.std(total_rewards),
            'mean_portfolio_value': np.mean(portfolio_values),
            'std_portfolio_value': np.std(portfolio_values)
        }
        
    def _sample_batch(self) -> Dict[str, np.ndarray]:
        """Sample a batch from the replay buffer."""
        indices = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
        batch = [self.replay_buffer[i] for i in indices]
        
        return {
            'state': {k: np.stack([b['state'][k] for b in batch]) for k in batch[0]['state'].keys()},
            'action': np.stack([b['action'] for b in batch]),
            'reward': np.stack([b['reward'] for b in batch]),
            'next_state': {k: np.stack([b['next_state'][k] for b in batch]) for k in batch[0]['next_state'].keys()},
            'done': np.stack([b['done'] for b in batch])
        }
        
    def save_model(self, path: str = "models/sac"):
        """Save the trained model."""
        os.makedirs(path, exist_ok=True)
        torch.save({
            'actor_state_dict': self.agent.actor.state_dict(),
            'critic1_state_dict': self.agent.critic1.state_dict(),
            'critic2_state_dict': self.agent.critic2.state_dict(),
            'target_critic1_state_dict': self.agent.target_critic1.state_dict(),
            'target_critic2_state_dict': self.agent.target_critic2.state_dict()
        }, os.path.join(path, "sac_model.pt"))
        
    def load_model(self, path: str = "models/sac/sac_model.pt"):
        """Load a trained model."""
        if os.path.exists(path):
            checkpoint = torch.load(path)
            self.agent.actor.load_state_dict(checkpoint['actor_state_dict'])
            self.agent.critic1.load_state_dict(checkpoint['critic1_state_dict'])
            self.agent.critic2.load_state_dict(checkpoint['critic2_state_dict'])
            self.agent.target_critic1.load_state_dict(checkpoint['target_critic1_state_dict'])
            self.agent.target_critic2.load_state_dict(checkpoint['target_critic2_state_dict'])
            logger.info("Model loaded successfully")
        else:
            logger.warning("No model found at specified path")

if __name__ == "__main__":
    # Initialize and train the trading system without LLM
    trading_system = TradingSystem(use_llm=False)
    trading_system.train()
    
    # Evaluate without LLM
    evaluation_results = trading_system.evaluate(use_llm=False)
    logger.info(f"Evaluation Results (SAC only): {evaluation_results}")
    
    # Save the trained model
    trading_system.save_model()
    
    # If LLM is available, evaluate with LLM validation
    if os.getenv('OPENAI_API_KEY'):
        trading_system.use_llm = True
        llm_evaluation_results = trading_system.evaluate(use_llm=True)
        logger.info(f"Evaluation Results (with LLM): {llm_evaluation_results}") 