import os
import yaml
import logging
import argparse
from dotenv import load_dotenv
from trading import TradingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging(config, mode, agent_type):
    """Setup logging configuration."""
    log_dir = os.path.join(config['logging']['save_path'], mode, agent_type)
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format=config['logging']['format'],
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'{mode}.log')),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def train_and_evaluate(config, agent_type: str):
    """Train a new model and evaluate it."""
    logger.info(f"Starting training and evaluation mode for {agent_type.upper()}...")
    
    try:
        # Get agent-specific config
        agent_config = config[agent_type.lower()]
        
        # Initialize trading system
        logger.info(f"Initializing trading system ({agent_type.upper()} only)...")
        trading_system = TradingSystem(
            initial_balance=config['environment']['initial_balance'],
            train_episodes=agent_config['train_episodes'],
            eval_episodes=agent_config['eval_episodes'],
            batch_size=agent_config['batch_size'],
            buffer_size=agent_config.get('buffer_size', 1000000),  # Only SAC uses buffer_size
            use_llm=False,
            agent_type=agent_type.lower()
        )
        
        # Train the model
        logger.info(f"Starting {agent_type.upper()} training...")
        trading_system.train()
        
        # Evaluate without LLM
        logger.info(f"Evaluating {agent_type.upper()} model performance...")
        evaluation_results = trading_system.evaluate(use_llm=False)
        logger.info(f"{agent_type.upper()} Evaluation Results: {evaluation_results}")
        
        # Save the trained model
        logger.info(f"Saving trained {agent_type.upper()} model...")
        trading_system.save_model()
        
        # If LLM is available, evaluate with LLM validation
        if os.getenv('GOOGLE_API_KEY'):
            logger.info("Evaluating with LLM validation...")
            trading_system.use_llm = True
            llm_evaluation_results = trading_system.evaluate(use_llm=True)
            logger.info(f"LLM Evaluation Results: {llm_evaluation_results}")
        
        logger.info(f"{agent_type.upper()} training and evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during {agent_type.upper()} training and evaluation: {str(e)}", exc_info=True)
        raise

def load_and_evaluate(config, agent_type: str):
    """Load a trained model and evaluate it."""
    logger.info(f"Starting load and evaluate mode for {agent_type.upper()}...")
    
    try:
        # Get agent-specific config
        agent_config = config[agent_type.lower()]
        
        # Initialize trading system
        logger.info(f"Initializing trading system ({agent_type.upper()} only)...")
        trading_system = TradingSystem(
            initial_balance=config['environment']['initial_balance'],
            train_episodes=0,  # No training in evaluation mode
            eval_episodes=agent_config['eval_episodes'],
            batch_size=agent_config['batch_size'],
            buffer_size=agent_config.get('buffer_size', 1000000),  # Only SAC uses buffer_size
            use_llm=False,
            agent_type=agent_type.lower()
        )
        
        # Load the trained model
        logger.info(f"Loading trained {agent_type.upper()} model...")
        trading_system.load_model()
        
        # Evaluate without LLM
        logger.info(f"Evaluating {agent_type.upper()} model performance...")
        evaluation_results = trading_system.evaluate(use_llm=False)
        logger.info(f"{agent_type.upper()} Evaluation Results: {evaluation_results}")
        
        # If LLM is available, evaluate with LLM validation
        if os.getenv('GOOGLE_API_KEY'):
            logger.info("Evaluating with LLM validation...")
            trading_system.use_llm = True
            llm_evaluation_results = trading_system.evaluate(use_llm=True)
            logger.info(f"LLM Evaluation Results: {llm_evaluation_results}")
        
        logger.info(f"{agent_type.upper()} load and evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during {agent_type.upper()} load and evaluation: {str(e)}", exc_info=True)
        raise

def main():
    """Main entry point for the trading system."""
    parser = argparse.ArgumentParser(description='Trading System')
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'evaluate'],
                      help='Mode to run the system in: train (train and evaluate) or evaluate (load and evaluate)')
    parser.add_argument('--agent', type=str, required=True, choices=['sac', 'ppo'],
                      help='Type of agent to use: sac or ppo')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                      help='Path to configuration file')
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config, args.mode, args.agent)
    
    if args.mode == 'train':
        train_and_evaluate(config, args.agent)
    else:  # evaluate
        load_and_evaluate(config, args.agent)

if __name__ == "__main__":
    main() 