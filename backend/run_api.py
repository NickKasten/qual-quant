import uvicorn
import logging
from pathlib import Path
from app.core.config import get_settings
from app.db.init_db import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / 'logs' / 'api.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Load configuration
        settings = get_settings()
        logger.info("Configuration loaded successfully")
        
        # Initialize database
        if not init_database():
            logger.error("Failed to initialize database")
            return
        
        # Start API server
        uvicorn.run(
            "app.api.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.DEBUG,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"API server startup failed: {e}", exc_info=True)

if __name__ == "__main__":
    main() 