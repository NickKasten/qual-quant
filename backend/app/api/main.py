"""
Main API module - imports the configured FastAPI app.
This maintains backward compatibility with existing imports.
"""
from .app import create_app

# Create the app instance for import by other modules
app = create_app() 