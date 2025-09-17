"""
Centralized logging configuration for the trading bot application.
Consolidates logging setup that was duplicated across multiple files.
"""
import os
import logging
from pathlib import Path
from typing import Optional, List


def setup_logging(
    service_name: str = "app",
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    include_file_handler: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for the application.
    
    Args:
        service_name: Name of the service for log file naming (e.g., 'api', 'trading', 'combined')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files (defaults to 'logs' in project root)
        include_file_handler: Whether to include file logging
        
    Returns:
        Configured logger instance
    """
    # Determine log directory
    if log_dir is None:
        # Default to logs directory relative to project root
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / 'logs'
    else:
        log_dir = Path(log_dir)
    
    # Create logs directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)
    
    # Setup handlers
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    
    # Add file handler if requested and possible
    if include_file_handler:
        try:
            log_file = log_dir / f'{service_name}.log'
            file_handler = logging.FileHandler(log_file)
            handlers.append(file_handler)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create {service_name} log file: {e}")
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized for {service_name} service")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)