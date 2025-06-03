import os
import yaml
import logging
from dotenv import load_dotenv
from trading import TradingSystem

def setup_logging(config):
    """Setup logging configuration."""
    os.makedirs(config['logging']['save_path'], exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format=config['logging']['format'],
        handlers=[
            logging.FileHandler(os.path.join(config['logging']['save_path'], 'trading.log')),
            logging.StreamHandler()
        ]
    )

def load_config():
    """Load configuration from YAML file."""
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize trading system without LLM
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
            logger.info("LLM API key found. Enabling LLM validation...")
            trading_system.use_llm = True
            
            # Evaluate with LLM validation
            logger.info("Evaluating with LLM validation...")
            llm_evaluation_results = trading_system.evaluate(use_llm=True)
            logger.info(f"Evaluation Results (with LLM): {llm_evaluation_results}")
        else:
            logger.warning("No OpenAI API key found. LLM validation will not be used.")
        
        logger.info("Trading system training and evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 