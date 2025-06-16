import uvicorn
from app.core.config import load_config

def main():
    config = load_config()
    host = config.get("API_HOST", "0.0.0.0")
    port = int(config.get("API_PORT", "8000"))
    
    uvicorn.run(
        "app.api.main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )

if __name__ == "__main__":
    main() 