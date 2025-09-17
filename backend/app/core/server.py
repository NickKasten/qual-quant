"""
Server factory functions for different application modes.
Consolidates server startup logic that was duplicated across multiple files.
"""
import os
import uvicorn
import threading
from http.server import HTTPServer
from typing import Optional

from .logging import setup_logging, get_logger


def create_health_server(port: int = 8080, handler_class=None):
    """
    Create a health check HTTP server.
    
    Args:
        port: Port to run health server on
        handler_class: HTTP handler class for health checks
        
    Returns:
        HTTPServer instance
    """
    if handler_class is None:
        from ..utils.health import HealthCheckHandler
        handler_class = HealthCheckHandler
    
    try:
        server = HTTPServer(('0.0.0.0', port), handler_class)
        logger = get_logger(__name__)
        logger.info(f"Health check server created on port {port}")
        return server
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to create health server: {e}")
        return None


def start_health_server_background(port: int = 8080, handler_class=None) -> Optional[threading.Thread]:
    """
    Start health check server in background thread.
    
    Args:
        port: Port to run health server on
        handler_class: HTTP handler class for health checks
        
    Returns:
        Thread instance if successful, None otherwise
    """
    def _run_health_server():
        server = create_health_server(port, handler_class)
        if server:
            server.serve_forever()
    
    try:
        thread = threading.Thread(target=_run_health_server, daemon=True)
        thread.start()
        return thread
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to start health server thread: {e}")
        return None


def create_api_server(host: str = "0.0.0.0", port: int = 8000, **kwargs):
    """
    Create API-only server configuration.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        **kwargs: Additional uvicorn configuration
        
    Returns:
        Dict with server configuration
    """
    setup_logging("api")
    logger = get_logger(__name__)
    
    # Import the FastAPI app
    from ..api.main import app
    
    # Test app initialization
    try:
        logger.info("Testing API app import...")
        logger.info(f"App routes: {len(app.routes)}")
        logger.info("API server initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing app: {e}")
        raise
    
    config = {
        'app': app,
        'host': host,
        'port': port,
        'workers': 1,
        'access_log': True,
        'log_level': "info",
        **kwargs
    }
    
    logger.info(f"API server configuration created for {host}:{port}")
    return config


def create_combined_server(host: str = "0.0.0.0", port: int = 8000, **kwargs):
    """
    Create combined API + background bot server configuration.
    
    Args:
        host: Host to bind to
        port: Port to bind to  
        **kwargs: Additional uvicorn configuration
        
    Returns:
        Dict with server configuration
    """
    setup_logging("combined")
    logger = get_logger(__name__)
    
    # Import the FastAPI app with background bot integration
    from ..api.main import app
    from ..services.background import background_bot
    
    # Add startup/shutdown events for background bot
    @app.on_event("startup")
    async def startup_event():
        try:
            logger.info("=== STARTUP EVENT TRIGGERED ===")
            logger.info("API server starting, launching background bot...")
            background_bot.start()
            logger.info("=== BACKGROUND BOT START CALLED ===")
        except Exception as e:
            logger.error(f"Error in startup event: {e}", exc_info=True)
            raise

    @app.on_event("shutdown") 
    async def shutdown_event():
        try:
            logger.info("=== SHUTDOWN EVENT TRIGGERED ===")
            logger.info("API server shutting down, stopping background bot...")
            background_bot.stop()
        except Exception as e:
            logger.error(f"Error in shutdown event: {e}", exc_info=True)
    
    # Test app initialization
    try:
        logger.info("Testing combined app import...")
        logger.info(f"App routes: {len(app.routes)}")
        logger.info("Combined server initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing app: {e}")
        raise
    
    config = {
        'app': app,
        'host': host,
        'port': port,
        'workers': 1,
        'access_log': True,
        'log_level': "info",
        **kwargs
    }
    
    logger.info(f"Combined server configuration created for {host}:{port}")
    return config


def run_api_server(host: str = "0.0.0.0", port: Optional[int] = None, **kwargs):
    """
    Run the API-only server.
    
    Args:
        host: Host to bind to
        port: Port to bind to (defaults to PORT env var or 8000)
        **kwargs: Additional uvicorn configuration
    """
    if port is None:
        port = int(os.environ.get("PORT", 8000))
    
    config = create_api_server(host, port, **kwargs)
    
    logger = get_logger(__name__)
    logger.info(f"Starting API server on {host}:{port}")
    
    uvicorn.run(**config)


def run_combined_server(host: str = "0.0.0.0", port: Optional[int] = None, **kwargs):
    """
    Run the combined API + background bot server.
    
    Args:
        host: Host to bind to
        port: Port to bind to (defaults to PORT env var or 8000)
        **kwargs: Additional uvicorn configuration
    """
    if port is None:
        port = int(os.environ.get("PORT", 8000))
    
    config = create_combined_server(host, port, **kwargs)
    
    logger = get_logger(__name__)
    logger.info(f"Starting combined API server + bot on {host}:{port}")
    
    # Manually start background bot before server
    from ..services.background import background_bot
    logger.info("=== MANUALLY STARTING BACKGROUND BOT ===")
    background_bot.start()
    
    uvicorn.run(**config)


def run_background_bot(symbols: str = "AAPL,MSFT,JNJ,UNH,V", 
                      interval: int = 300,
                      max_loops: Optional[int] = None,
                      health_port: int = 8080):
    """
    Run only the background trading bot with health server.
    
    Args:
        symbols: Comma-separated trading symbols
        interval: Trading cycle interval in seconds
        max_loops: Maximum number of cycles (for testing)
        health_port: Port for health check server
    """
    setup_logging("trading")
    logger = get_logger(__name__)
    
    # Start health check server
    start_health_server_background(health_port)
    
    # Run background bot
    from ..services.background import run_background_bot_loop
    run_background_bot_loop(symbols, interval, max_loops)
