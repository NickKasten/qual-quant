import os
import yaml
import logging
import argparse
from dotenv import load_dotenv
from trading import TradingSystem

def setup_logging(config, mode):
    """Setup logging configuration."""
    log_dir = os.path.join(config['logging']['save_path'], mode)
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format=config['logging']['format'],
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'{mode}.log')),
            logging.StreamHandler()
        ]
    )

def load_config():
    """Load configuration from YAML file."""
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config

def train_mode(config):
    """Run the system in training mode."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize trading system without LLM for training
        logger.info("Initializing trading system (SAC only)...")
        trading_system = TradingSystem(
            initial_balance=config['environment']['initial_balance'],
            train_episodes=config['sac']['train_episodes'],
            eval_episodes=config['sac']['eval_episodes'],
            batch_size=config['sac']['batch_size'],
            buffer_size=config['sac']['buffer_size'],
            use_llm=False
        )
        
        # Train the SAC model
        logger.info("Starting SAC training...")
        trading_system.train()
        
        # Evaluate SAC model without LLM
        logger.info("Evaluating SAC model performance...")
        sac_evaluation_results = trading_system.evaluate(use_llm=False)
        logger.info(f"SAC Evaluation Results: {sac_evaluation_results}")
        
        # Save the trained SAC model
        logger.info("Saving trained SAC model...")
        trading_system.save_model(path=config['logging']['model_save_path'])
        
        logger.info("Training completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during training: {str(e)}", exc_info=True)
        raise

def live_mode(config):
    """Run the system in live trading mode with LLM validation."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize trading system with LLM
        logger.info("Initializing trading system (SAC + LLM)...")
        trading_system = TradingSystem(
            initial_balance=config['environment']['initial_balance'],
            train_episodes=0,  # No training in live mode
            eval_episodes=1,   # Single episode for live trading
            batch_size=config['sac']['batch_size'],
            buffer_size=config['sac']['buffer_size'],
            use_llm=True
        )
        
        # Load the trained model
        logger.info("Loading trained SAC model...")
        trading_system.load_model(path=config['logging']['model_save_path'])
        
        # Run live trading
        logger.info("Starting live trading with LLM validation...")
        results = trading_system.evaluate(use_llm=True)
        logger.info(f"Live Trading Results: {results}")
        
        logger.info("Live trading completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during live trading: {str(e)}", exc_info=True)
        raise

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Trading System')
    parser.add_argument('--mode', choices=['train', 'live'], required=True,
                      help='Mode to run the system in: train or live')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config, args.mode)
    
    # Run in selected mode
    if args.mode == 'train':
        train_mode(config)
    else:
        live_mode(config)

if __name__ == "__main__":
    main() 