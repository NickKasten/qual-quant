import os
import logging
import requests
import time
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class FailureMonitor:
    """
    Lightweight monitoring system for persistent trading bot failures.
    Tracks consecutive failures and sends alerts when threshold is exceeded.
    """
    
    def __init__(self, max_consecutive_failures: int = 3):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.last_success_time = None
        self.last_alert_time = None
        self.alert_cooldown = 3600  # 1 hour between alerts
        
        # Alert configuration from environment
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.email_webhook_url = os.getenv("EMAIL_WEBHOOK_URL")
        
    def record_success(self):
        """Record a successful trading cycle."""
        if self.consecutive_failures > 0:
            logger.info(f"✅ Recovery: Reset failure count from {self.consecutive_failures} to 0")
        
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        
    def record_failure(self, error_message: str = ""):
        """Record a failed trading cycle and check if alert should be sent."""
        self.consecutive_failures += 1
        logger.warning(f"⚠️  Failure #{self.consecutive_failures}: {error_message}")
        
        if self.consecutive_failures >= self.max_consecutive_failures:
            self._send_alert(error_message)
            
    def _send_alert(self, error_message: str):
        """Send alert for persistent failures."""
        current_time = time.time()
        
        # Check cooldown period
        if (self.last_alert_time and 
            current_time - self.last_alert_time < self.alert_cooldown):
            logger.info(f"Alert suppressed due to cooldown period")
            return
            
        alert_message = self._create_alert_message(error_message)
        
        # Try Slack webhook first
        if self.webhook_url:
            try:
                self._send_slack_alert(alert_message)
                self.last_alert_time = current_time
                return
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
                
        # Try email webhook as fallback
        if self.email_webhook_url:
            try:
                self._send_email_alert(alert_message)
                self.last_alert_time = current_time
                return
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
                
        # Log alert if no webhooks available
        logger.critical(f"🚨 ALERT: {alert_message}")
        self.last_alert_time = current_time
        
    def _create_alert_message(self, error_message: str) -> str:
        """Create formatted alert message."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        uptime_hours = (time.time() - self.last_success_time) / 3600 if self.last_success_time else None
        uptime_str = f"{uptime_hours:.1f}" if uptime_hours is not None else "unknown"
        
        return (
            f"🚨 TRADING BOT FAILURE ALERT\n"
            f"Time: {timestamp}\n"
            f"Consecutive failures: {self.consecutive_failures}\n"
            f"Hours since last success: {uptime_str}\n"
            f"Latest error: {error_message or 'No specific error message'}\n"
            f"Environment: {os.getenv('RENDER_SERVICE_NAME', 'local')}"
        )
        
    def _send_slack_alert(self, message: str):
        """Send alert to Slack webhook."""
        payload = {
            "text": message,
            "username": "Trading Bot Monitor",
            "icon_emoji": ":warning:"
        }
        
        response = requests.post(
            self.webhook_url, 
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info("✅ Slack alert sent successfully")
        
    def _send_email_alert(self, message: str):
        """Send alert via email webhook (generic format)."""
        payload = {
            "subject": "Trading Bot Failure Alert",
            "body": message,
            "priority": "high"
        }
        
        response = requests.post(
            self.email_webhook_url,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info("✅ Email alert sent successfully")
        
    def get_status(self) -> dict:
        """Get current monitoring status."""
        return {
            "consecutive_failures": self.consecutive_failures,
            "last_success_time": self.last_success_time,
            "last_alert_time": self.last_alert_time,
            "max_consecutive_failures": self.max_consecutive_failures,
            "webhook_configured": bool(self.webhook_url or self.email_webhook_url)
        }

# Global monitor instance
monitor = FailureMonitor()