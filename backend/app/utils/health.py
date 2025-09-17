"""
Health check handler for HTTP health endpoints.
Extracted from main.py to be reusable across different server modes.
"""
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

from ..core.logging import get_logger
from ..services.background import bot_status


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks and status monitoring."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        logger = get_logger(__name__)
        
        try:
            if self.path == '/health':
                # Health check endpoint
                uptime = datetime.now(timezone.utc) - bot_status['uptime_start']
                
                response = {
                    'status': 'healthy',
                    'bot_status': bot_status['status'],
                    'uptime_seconds': int(uptime.total_seconds()),
                    'cycles_completed': bot_status['cycles_completed'],
                    'market_open': bot_status['market_open'],
                    'last_cycle_time': bot_status['last_cycle_time'].isoformat() if bot_status['last_cycle_time'] else None,
                    'next_cycle_time': bot_status['next_cycle_time'].isoformat() if bot_status['next_cycle_time'] else None
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            elif self.path == '/':
                # Root endpoint
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Trading Bot is running')
                
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format_str, *args):
        """Suppress default HTTP logging to avoid log spam."""
        pass