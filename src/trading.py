import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import torch
from tqdm import tqdm
import yaml

from data_collection import DataCollector
from environment import TradingEnvironment
from sac_agent import SACAgent
from ppo_agent import PPOAgent, PPOMemory
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
                 initial_balance: float,
                 train_episodes: int,
                 eval_episodes: int,
                 batch_size: int,
                 buffer_size: int,
                 use_llm: bool = False,
                 agent_type: str = 'sac'):
        """
        Initialize the trading system.
        
        Args:
            initial_balance: Initial portfolio balance
            train_episodes: Number of training episodes
            eval_episodes: Number of evaluation episodes
            batch_size: Batch size for training
            buffer_size: Size of replay buffer
            use_llm: Whether to use LLM validation
            agent_type: Type of agent to use ('sac' or 'ppo')
        """
        self.initial_balance = initial_balance
        self.train_episodes = train_episodes
        self.eval_episodes = eval_episodes
        self.batch_size = batch_size
        self.buffer_size = buffer_size
        self.use_llm = use_llm
        self.agent_type = agent_type.lower()
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.data_collector = DataCollector()
        self.environment = None
        self.agent = None
        self.llm_validator = None if not use_llm else LLMValidator()
        
        # Initialize memory for PPO
        self.memory = PPOMemory(batch_size) if self.agent_type == 'ppo' else None
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        config_path = os.path.join('config', 'config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _initialize_environment(self, data: Dict[str, pd.DataFrame]):
        """Initialize the trading environment."""
        self.environment = TradingEnvironment(
            data=data,
            initial_balance=self.initial_balance
        )
        
    def _initialize_agent(self):
        """Initialize the trading agent."""
        if self.agent_type == 'sac':
            self.agent = SACAgent(
                state_dim=self.environment.observation_space,
                action_dim=len(self.environment.tickers),
                hidden_dim=self.config['sac']['hidden_dim']
            )
        elif self.agent_type == 'ppo':
            self.agent = PPOAgent(
                state_dim=self.environment.observation_space,
                action_dim=len(self.environment.tickers),
                hidden_dim=self.config['ppo']['hidden_dim'],
                learning_rate=self.config['ppo']['learning_rate'],
                gamma=self.config['ppo']['gamma'],
                gae_lambda=self.config['ppo']['gae_lambda'],
                epsilon=self.config['ppo']['epsilon']
            )
        else:
            raise ValueError(f"Unsupported agent type: {self.agent_type}")
            
    def train(self, refresh_data: bool = False):
        """Train the trading agent."""
        logger.info(f"Starting training with {self.agent_type.upper()} agent...")
        
        # Collect and prepare data
        data = self.data_collector.get_training_data(refresh=refresh_data)
        self._initialize_environment(data)
        self._initialize_agent()
        
        # Training loop
        for episode in tqdm(range(self.train_episodes), desc='Training Episodes'):
            state = self.environment.reset()
            episode_reward = 0
            done = False
            
            while not done:
                # Get action from agent
                if self.agent_type == 'sac':
                    action = self.agent.select_action(state)
                else:  # PPO
                    action, log_prob = self.agent.select_action(state)
                    # Flatten and concatenate state for critic and memory
                    state_tensor = torch.cat([
                        torch.FloatTensor(state[k]).flatten().to(self.agent.device)
                        for k in state.keys()
                    ])
                    value = self.agent.critic(state_tensor).detach().cpu().numpy()
                
                # Apply LLM validation if enabled
                if self.use_llm:
                    action = self.llm_validator.validate_decision(
                        action,
                        self.environment.tickers,
                        datetime.now(),  # Use current date for live trading
                        data
                    )
                
                # Execute action
                next_state, reward, done, info = self.environment.step(action)
                episode_reward += reward
                
                # Store transition
                if self.agent_type == 'sac':
                    # SAC uses a replay buffer internally
                    pass
                else:  # PPO
                    self.memory.store_memory(
                        state=state_tensor.cpu().numpy(),
                        action=action,
                        probs=log_prob,
                        vals=value,
                        reward=reward,
                        done=done
                    )
                
                state = next_state
            
            logger.info(f"Episode {episode + 1} completed with reward: {episode_reward}")
            
        # Save the trained model
        self.save_model()
        
    def evaluate(self, use_llm: bool = None) -> Dict:
        """Evaluate the trading agent."""
        if use_llm is not None:
            self.use_llm = use_llm
            
        logger.info(f"Starting evaluation with {self.agent_type.upper()} agent...")
        
        # Collect and prepare data
        data = self.data_collector.collect_historical_data()
        self._initialize_environment(data)
        self._initialize_agent()
        
        # Load the trained model
        self.load_model()
        
        # Evaluation metrics
        total_rewards = []
        final_portfolio_values = []
        sharpe_ratios = []
        
        # Evaluation loop
        for episode in range(self.eval_episodes):
            state = self.environment.reset()
            episode_reward = 0
            done = False
            portfolio_values = []
            
            while not done:
                # Get action from agent
                action = self.agent.select_action(state, evaluate=True)
                
                # Apply LLM validation if enabled
                if self.use_llm:
                    action = self.llm_validator.validate_decision(
                        action,
                        self.environment.tickers,
                        datetime.now(),
                        data
                    )
                
                # Execute action
                next_state, reward, done, info = self.environment.step(action)
                episode_reward += reward
                portfolio_values.append(info['portfolio_value'])
                
                state = next_state
            
            # Calculate metrics
            total_rewards.append(episode_reward)
            final_portfolio_values.append(portfolio_values[-1])
            
            # Calculate Sharpe ratio
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
            sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns)
            sharpe_ratios.append(sharpe_ratio)
            
            logger.info(f"Evaluation episode {episode + 1} completed with reward: {episode_reward}")
            
        # Calculate aggregate metrics
        results = {
            'mean_reward': np.mean(total_rewards),
            'std_reward': np.std(total_rewards),
            'mean_final_portfolio': np.mean(final_portfolio_values),
            'std_final_portfolio': np.std(final_portfolio_values),
            'mean_sharpe_ratio': np.mean(sharpe_ratios),
            'std_sharpe_ratio': np.std(sharpe_ratios)
        }
        
        logger.info(f"Evaluation results: {results}")
        return results
        
    def save_model(self, path: str = None):
        """Save the trained model."""
        if path is None:
            path = os.path.join(self.config['logging']['model_save_path'], f"{self.agent_type}_model.pt")
            
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.agent.save(path)
            logger.info(f"Model saved successfully to {path}")
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
        
    def load_model(self, path: str = None):
        """Load a trained model."""
        if path is None:
            path = os.path.join(self.config['logging']['model_save_path'], f"{self.agent_type}_model.pt")
            
        try:
            self.agent.load(path)
            logger.info(f"Model loaded successfully from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

if __name__ == "__main__":
    # Initialize and train the trading system with PPO
    trading_system = TradingSystem(
        initial_balance=100000.0,  # Starting with $100,000
        train_episodes=1000,       # Number of training episodes
        eval_episodes=100,         # Number of evaluation episodes
        batch_size=64,            # Batch size for training
        buffer_size=10000,        # Size of replay buffer
        use_llm=False,            # Don't use LLM validation initially
        agent_type='ppo'          # Use PPO agent
    )
    trading_system.train(refresh_data=False)
    
    # Evaluate without LLM
    evaluation_results = trading_system.evaluate(use_llm=False)
    logger.info(f"Evaluation Results (PPO only): {evaluation_results}")
    
    # Save the trained model
    trading_system.save_model()
    
    # If LLM is available, evaluate with LLM validation
    if os.getenv('OPENAI_API_KEY'):
        trading_system.use_llm = True
        llm_evaluation_results = trading_system.evaluate(use_llm=True)
        logger.info(f"Evaluation Results (with LLM): {llm_evaluation_results}") 