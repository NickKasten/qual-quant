import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import torch
from tqdm import tqdm

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
            try:
                self.llm_validator = LLMValidator()
                logger.info("LLM validator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LLM validator: {e}")
                raise
        
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
        
        # Initialize training metrics
        self.training_metrics = {
            'episode_rewards': [],
            'policy_entropy': [],
            'value_loss': [],
            'policy_loss': [],
            'q_values': [],
            'alpha_loss': []
        }
        
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
                        
            # Find common date range where all tickers have data
            if market_data:
                # Get the intersection of all date ranges
                # Normalize all indices to UTC
                for df in market_data.values():
                    # Ensure index is DatetimeIndex and UTC
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index, utc=True)
                    elif df.index.tz is None:
                        df.index = df.index.tz_localize('UTC')
                    else:
                        df.index = df.index.tz_convert('UTC')
                common_start = max(df.index.min() for df in market_data.values() if not df.empty)
                common_end = min(df.index.max() for df in market_data.values() if not df.empty)
                
                if common_start and common_end:
                    logger.info(f"Common date range: {common_start} to {common_end}")
                    # Filter data to only include the common date range
                    for ticker in market_data:
                        market_data[ticker] = market_data[ticker][common_start:common_end]
                        
                    # Verify all dataframes have the same number of unique dates
                    # For AAPL, we expect twice as many rows due to dual timestamps
                    unique_dates = {ticker: len(df.index.date.unique()) for ticker, df in market_data.items()}
                    if len(set(unique_dates.values())) != 1:
                        logger.warning(f"Number of unique dates after filtering: {unique_dates}")
                        # Find the minimum number of unique dates and trim all dataframes to that
                        min_unique_dates = min(unique_dates.values())
                        for ticker in market_data:
                            # For AAPL, keep both timestamps for each date
                            if ticker == 'AAPL':
                                dates_to_keep = sorted(market_data[ticker].index.date.unique())[-min_unique_dates:]
                                market_data[ticker] = market_data[ticker][market_data[ticker].index.date.isin(dates_to_keep)]
                            else:
                                # For other tickers, trim to the minimum number of unique dates
                                dates_to_keep = sorted(market_data[ticker].index.date.unique())[-min_unique_dates:]
                                market_data[ticker] = market_data[ticker][market_data[ticker].index.date.isin(dates_to_keep)]
                        
                        # Log the final data lengths
                        data_lengths = {ticker: len(df) for ticker, df in market_data.items()}
                        logger.info(f"Data lengths after filtering: {data_lengths}")
                        
                        # For AAPL, we expect twice as many rows as other tickers
                        if data_lengths['AAPL'] != 2 * data_lengths['MSFT']:
                            logger.warning(f"AAPL data length ({data_lengths['AAPL']}) is not twice MSFT's length ({data_lengths['MSFT']})")
                else:
                    logger.warning("No common date range found for all tickers")
                    
            return market_data
        else:
            logger.info("Collecting new data...")
            return self.data_collector.collect_historical_data()
            
    def train(self):
        """Train the SAC agent with comprehensive monitoring."""
        logger.info("Starting SAC training...")
        
        # Create progress bar for episodes
        pbar = tqdm(range(self.train_episodes), desc="Training Episodes")
        
        for episode in pbar:
            state = self.env.reset()
            episode_reward = 0
            done = False
            episode_metrics = {
                'policy_entropy': [],
                'value_loss': [],
                'policy_loss': [],
                'q_values': [],
                'alpha_loss': []
            }
            
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
                    
                    # Track metrics
                    episode_metrics['policy_entropy'].append(losses.get('policy_entropy', 0))
                    episode_metrics['value_loss'].append(losses.get('critic1_loss', 0) + losses.get('critic2_loss', 0))
                    episode_metrics['policy_loss'].append(losses.get('actor_loss', 0))
                    episode_metrics['q_values'].append(losses.get('q_value', 0))
                    episode_metrics['alpha_loss'].append(losses.get('alpha_loss', 0))
                
                state = next_state
                episode_reward += reward
            
            # Store episode metrics
            self.training_metrics['episode_rewards'].append(episode_reward)
            for metric in episode_metrics:
                if episode_metrics[metric]:
                    self.training_metrics[metric].append(np.mean(episode_metrics[metric]))
            
            # Calculate moving averages for monitoring
            reward_ma = np.mean(self.training_metrics['episode_rewards'][-10:]) if len(self.training_metrics['episode_rewards']) >= 10 else episode_reward
            entropy_ma = np.mean(self.training_metrics['policy_entropy'][-10:]) if len(self.training_metrics['policy_entropy']) >= 10 else 0
            
            # Update progress bar with comprehensive metrics
            pbar.set_postfix({
                'reward': f'{episode_reward:.2f}',
                'reward_ma': f'{reward_ma:.2f}',
                'entropy': f'{entropy_ma:.2f}'
            })
            
            # Log detailed metrics every 10 episodes
            if episode % 10 == 0:
                logger.info(f"Episode {episode} Metrics:")
                logger.info(f"  Total Reward: {episode_reward:.2f}")
                logger.info(f"  10-Episode Moving Average Reward: {reward_ma:.2f}")
                logger.info(f"  Policy Entropy: {entropy_ma:.2f}")
                if episode_metrics['value_loss']:
                    logger.info(f"  Value Loss: {np.mean(episode_metrics['value_loss']):.4f}")
                if episode_metrics['policy_loss']:
                    logger.info(f"  Policy Loss: {np.mean(episode_metrics['policy_loss']):.4f}")
                if episode_metrics['q_values']:
                    logger.info(f"  Q-Value: {np.mean(episode_metrics['q_values']):.4f}")
        
        # Save training metrics
        self._save_training_metrics()
        
    def _save_training_metrics(self):
        """Save training metrics to a CSV file."""
        metrics_df = pd.DataFrame(self.training_metrics)
        metrics_path = os.path.join("data/training_metrics", "sac_training_metrics.csv")
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        metrics_df.to_csv(metrics_path, index=False)
        logger.info(f"Training metrics saved to {metrics_path}")
        
        # Create and save plots
        self._plot_training_metrics(metrics_df)
        
    def _plot_training_metrics(self, metrics_df):
        """Create and save plots of training metrics."""
        import matplotlib.pyplot as plt
        
        # Create plots directory
        plots_dir = "data/training_plots"
        os.makedirs(plots_dir, exist_ok=True)
        
        # Plot rewards
        plt.figure(figsize=(10, 6))
        plt.plot(metrics_df['episode_rewards'], label='Episode Reward')
        plt.plot(metrics_df['episode_rewards'].rolling(10).mean(), label='10-Episode Moving Average')
        plt.title('Training Rewards')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.legend()
        plt.savefig(os.path.join(plots_dir, 'rewards.png'))
        plt.close()
        
        # Plot policy entropy
        plt.figure(figsize=(10, 6))
        plt.plot(metrics_df['policy_entropy'], label='Policy Entropy')
        plt.title('Policy Entropy During Training')
        plt.xlabel('Episode')
        plt.ylabel('Entropy')
        plt.legend()
        plt.savefig(os.path.join(plots_dir, 'entropy.png'))
        plt.close()
        
        # Plot losses
        plt.figure(figsize=(10, 6))
        plt.plot(metrics_df['value_loss'], label='Value Loss')
        plt.plot(metrics_df['policy_loss'], label='Policy Loss')
        plt.title('Training Losses')
        plt.xlabel('Episode')
        plt.ylabel('Loss')
        plt.legend()
        plt.savefig(os.path.join(plots_dir, 'losses.png'))
        plt.close()
        
        logger.info(f"Training plots saved to {plots_dir}")
        
    def evaluate(self, use_llm: bool = None) -> Dict[str, float]:
        """Evaluate the trained agent with optional LLM validation."""
        if use_llm is None:
            use_llm = self.use_llm
            
        logger.info(f"Starting evaluation with LLM validation: {use_llm}")
        
        total_rewards = []
        portfolio_values = []
        sac_rewards = []  # Track rewards without LLM validation
        validation_history = []  # Track LLM validation decisions
        
        for episode in range(self.eval_episodes):
            state = self.env.reset()
            episode_reward = 0
            sac_episode_reward = 0
            done = False
            
            while not done:
                # Get SAC decision
                action = self.agent.select_action(state, evaluate=True)
                
                if use_llm:
                    try:
                        # Get LLM validation
                        validated_action = self.llm_validator.validate_decision(
                            action,
                            self.env.tickers,
                            self.env.data[self.env.tickers[0]].index[self.env.current_step],
                            self.market_data
                        )
                        
                        # Execute validated action
                        next_state, reward, done, info = self.env.step(validated_action)
                        
                        # Record validation history
                        validation_history.append({
                            'ticker': self.env.tickers[0],
                            'date': self.env.data[self.env.tickers[0]].index[self.env.current_step],
                            'sac_action': action,
                            'validated_action': validated_action,
                            'reward': reward
                        })
                    except Exception as e:
                        logger.error(f"LLM validation failed: {e}")
                        # Fallback to SAC action
                        next_state, reward, done, info = self.env.step(action)
                else:
                    # Execute SAC action directly
                    next_state, reward, done, info = self.env.step(action)
                
                state = next_state
                episode_reward += reward
                
                if done:
                    portfolio_values.append(info['portfolio_value'])
            
            total_rewards.append(episode_reward)
            
        # Save validation history if LLM was used
        if use_llm and validation_history:
            history_df = pd.DataFrame(validation_history)
            history_path = os.path.join("data/validation_history", "live_validation_history.csv")
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            history_df.to_csv(history_path, index=False)
            logger.info(f"Validation history saved to {history_path}")
        
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
        """Save the trained SAC model and environment state."""
        os.makedirs(path, exist_ok=True)
        
        # Save SAC model
        model_path = os.path.join(path, "sac_model.pt")
        self.agent.save(model_path)
        logger.info(f"SAC model saved to {model_path}")
        
        # Save environment state
        env_state = {
            'market_data': self.market_data,
            'tickers': self.env.tickers,
            'initial_balance': self.initial_balance
        }
        env_path = os.path.join(path, "env_state.pt")
        torch.save(env_state, env_path)
        logger.info(f"Environment state saved to {env_path}")
        
    def load_model(self, path: str = "models/sac"):
        """Load the trained SAC model and environment state."""
        # Load SAC model
        model_path = os.path.join(path, "sac_model.pt")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"SAC model not found at {model_path}")
        self.agent.load(model_path)
        logger.info(f"SAC model loaded from {model_path}")
        
        # Load environment state
        env_path = os.path.join(path, "env_state.pt")
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"Environment state not found at {env_path}")
        env_state = torch.load(env_path)
        
        # Update environment with saved state
        self.market_data = env_state['market_data']
        self.env = TradingEnvironment(self.market_data, env_state['initial_balance'])
        logger.info(f"Environment state loaded from {env_path}")

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