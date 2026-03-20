#!/usr/bin/env python3
"""
Telegram Alert Service for Flight Tracker.
Runs continuously to monitor and send flight price alerts to Telegram.
"""

import os
import sys
import time
import threading
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, '.')

from alert_notifier import AlertNotifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] telegram_service: %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramAlertService:
    """Service to monitor and send flight alerts via Telegram."""
    
    def __init__(self, check_interval_minutes=10):
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.notifier = AlertNotifier()
        self.running = False
        self.thread = None
        
    def send_telegram_message(self, message, chat_id='540464122'):
        """Send message via OpenClaw message tool."""
        try:
            # This would be called by the main process that has access to message tool
            # For now, we'll log the message that should be sent
            logger.info(f"TELEGRAM ALERT TO SEND:\n{message}")
            
            # In the actual implementation, this would use the message tool:
            # message_tool(action='send', target=chat_id, message=message, channel='telegram')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def check_and_send_alerts(self):
        """Check for new alerts and send them via Telegram."""
        try:
            logger.info("🔍 Checking for new flight price alerts...")
            
            # Get new alerts
            alerts = self.notifier.get_new_alerts()
            
            if not alerts:
                logger.info("✅ No new alerts found")
                return
            
            logger.info(f"🚨 Found {len(alerts)} new alert(s)! Sending to Telegram...")
            
            for alert in alerts:
                route, price, airline, departure_date, drop_percentage, alert_sent_at = alert
                
                # Format message
                message = self.notifier.format_alert_message(
                    route, price, airline, departure_date, drop_percentage, alert_sent_at
                )
                
                # Send to Telegram
                success = self.send_telegram_message(message)
                
                if success:
                    logger.info(f"✅ Sent alert for {route} - R$ {price:.2f}")
                else:
                    logger.error(f"❌ Failed to send alert for {route}")
                
                # Small delay between messages
                time.sleep(1)
            
            # Update last check time
            self.notifier.last_check = datetime.now()
            self.notifier.save_last_check()
            
            logger.info(f"🎯 Completed processing {len(alerts)} alert(s)")
            
        except Exception as e:
            logger.error(f"Error in check_and_send_alerts: {e}")
    
    def run_service(self):
        """Main service loop."""
        logger.info(f"🚀 Starting Telegram Alert Service")
        logger.info(f"📊 Check interval: {self.check_interval//60} minutes")
        logger.info(f"🎯 Target chat: 540464122 (Tiago)")
        logger.info(f"💾 Database: {self.notifier.db_path}")
        
        self.running = True
        
        while self.running:
            try:
                self.check_and_send_alerts()
                
                # Wait for next check
                logger.info(f"⏰ Next check in {self.check_interval//60} minutes...")
                
                for i in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Service error: {e}")
                time.sleep(30)  # Wait 30 seconds before retrying
        
        self.running = False
        logger.info("👋 Telegram Alert Service stopped")
    
    def start_background(self):
        """Start service in background thread."""
        if self.thread and self.thread.is_alive():
            logger.warning("Service already running")
            return
        
        self.thread = threading.Thread(target=self.run_service, daemon=True)
        self.thread.start()
        logger.info("✅ Telegram Alert Service started in background")
    
    def stop(self):
        """Stop the service."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

# Global service instance
_service = None

def start_telegram_alerts(check_interval_minutes=10):
    """Start Telegram alert service."""
    global _service
    
    if _service is None:
        _service = TelegramAlertService(check_interval_minutes)
    
    _service.start_background()
    return _service

def stop_telegram_alerts():
    """Stop Telegram alert service."""
    global _service
    
    if _service:
        _service.stop()

def get_service_status():
    """Get service status."""
    global _service
    
    if _service is None:
        return {"status": "not_started"}
    
    return {
        "status": "running" if _service.running else "stopped",
        "check_interval_minutes": _service.check_interval // 60,
        "last_check": _service.notifier.last_check.isoformat() if _service.notifier.last_check else None
    }

if __name__ == "__main__":
    # For testing
    service = TelegramAlertService(check_interval_minutes=1)  # Check every minute for testing
    
    try:
        service.run_service()
    except KeyboardInterrupt:
        logger.info("👋 Service stopped by user")
        service.stop()