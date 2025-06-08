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

def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def train_and_evaluate(config):
    """Train a new model and evaluate it."""
    logger.info("Starting training and evaluation mode...")
    
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
        
        # If LLM is available, evaluate with LLM validation
        if os.getenv('OPENAI_API_KEY'):
            logger.info("Evaluating with LLM validation...")
            trading_system.use_llm = True
            llm_evaluation_results = trading_system.evaluate(use_llm=True)
            logger.info(f"LLM Evaluation Results: {llm_evaluation_results}")
        
        logger.info("Training and evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during training and evaluation: {str(e)}", exc_info=True)
        raise

def load_and_evaluate(config):
    """Load a trained model and evaluate it."""
    logger.info("Starting load and evaluate mode...")
    
    try:
        # Initialize trading system
        logger.info("Initializing trading system...")
        trading_system = TradingSystem(
            initial_balance=config['environment']['initial_balance'],
            train_episodes=0,  # No training in evaluation mode
            eval_episodes=config['sac']['eval_episodes'],
            batch_size=config['sac']['batch_size'],
            buffer_size=config['sac']['buffer_size'],
            use_llm=False
        )
        
        # Load the trained model
        logger.info("Loading trained SAC model...")
        trading_system.load_model(path=config['logging']['model_save_path'])
        
        # Evaluate without LLM
        logger.info("Evaluating SAC model performance...")
        sac_evaluation_results = trading_system.evaluate(use_llm=False)
        logger.info(f"SAC Evaluation Results: {sac_evaluation_results}")
        
        # If LLM is available, evaluate with LLM validation
        if os.getenv('OPENAI_API_KEY'):
            logger.info("Evaluating with LLM validation...")
            trading_system.use_llm = True
            llm_evaluation_results = trading_system.evaluate(use_llm=True)
            logger.info(f"LLM Evaluation Results: {llm_evaluation_results}")
        
        logger.info("Load and evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred during load and evaluation: {str(e)}", exc_info=True)
        raise

def main():
    """Main entry point for the trading system."""
    parser = argparse.ArgumentParser(description='Trading System')
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'evaluate'],
                      help='Mode to run the system in: train (train and evaluate) or evaluate (load and evaluate)')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                      help='Path to configuration file')
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config, args.mode)
    
    if args.mode == 'train':
        train_and_evaluate(config)
    else:  # evaluate
        load_and_evaluate(config)

if __name__ == "__main__":
    main() 