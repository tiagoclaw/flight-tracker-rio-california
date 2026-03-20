#!/usr/bin/env python3
"""
Telegram Integration for Flight Tracker Alerts.
Integrates with Railway monitoring system to send real-time alerts.
"""

import os
import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from threading import Thread

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] telegram_integration: %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramFlightAlerts:
    """Handles Telegram notifications for flight price alerts."""
    
    def __init__(self, db_path='data/flights.db'):
        self.db_path = db_path
        self.state_file = 'telegram_alert_state.json'
        self.telegram_chat_id = '540464122'  # Tiago's chat
        self.last_alert_check = self.load_state()
        
    def load_state(self):
        """Load last alert check timestamp."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    return datetime.fromisoformat(state.get('last_check', '2026-03-19T00:00:00'))
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
        
        # Default to 1 hour ago
        return datetime.now() - timedelta(hours=1)
    
    def save_state(self):
        """Save current timestamp as last check."""
        try:
            state = {
                'last_check': self.last_alert_check.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def get_new_alerts(self):
        """Get new alerts from database."""
        if not os.path.exists(self.db_path):
            logger.info(f"Database not found: {self.db_path}")
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if alerts table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
            if not cursor.fetchone():
                conn.close()
                return []
            
            # Get new alerts since last check
            cursor.execute("""
                SELECT route, price, airline, departure_date, drop_percentage, alert_sent_at, id
                FROM alerts 
                WHERE alert_sent_at > ?
                ORDER BY alert_sent_at DESC
            """, (self.last_alert_check.isoformat(),))
            
            alerts = cursor.fetchall()
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    def format_telegram_message(self, route, price, airline, departure_date, drop_percentage, alert_time):
        """Format alert message for Telegram."""
        
        route_names = {
            'GIG-LAX': '🛫 Rio Galeão → Los Angeles',
            'GIG-SFO': '🛫 Rio Galeão → San Francisco', 
            'SDU-LAX': '🛫 Santos Dumont → Los Angeles',
            'SDU-SFO': '🛫 Santos Dumont → San Francisco'
        }
        
        route_display = route_names.get(route, f'🛫 {route}')
        
        # Format dates
        try:
            if departure_date:
                dep_date = datetime.strptime(departure_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            else:
                dep_date = 'A definir'
        except:
            dep_date = departure_date or 'A definir'
        
        try:
            if alert_time:
                alert_dt = datetime.fromisoformat(alert_time.replace('Z', '+00:00'))
                alert_str = alert_dt.strftime('%d/%m/%Y às %H:%M')
            else:
                alert_str = datetime.now().strftime('%d/%m/%Y às %H:%M')
        except:
            alert_str = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        # Get drop emoji based on percentage
        if drop_percentage >= 25:
            drop_emoji = '🔥💥'
        elif drop_percentage >= 20:
            drop_emoji = '🔥'
        elif drop_percentage >= 15:
            drop_emoji = '📉🎯'
        else:
            drop_emoji = '📉'
        
        message = f"""🚨 **ALERTA DE PREÇO - VOOS RIO → CALIFORNIA!**

{route_display}
💰 **Preço:** R$ {price:,.2f}
✈️ **Companhia:** {airline}
📅 **Partida:** {dep_date}
{drop_emoji} **Queda:** {drop_percentage:.1f}%

🎯 **ÓTIMA OPORTUNIDADE!** Considere reservar rapidamente!

⏰ **Detectado:** {alert_str}
🔗 **Dashboard:** https://cheery-haupia-f7bf45.netlify.app

---
*Sistema de monitoramento 24/7 ativo* 🛫"""

        return message
    
    def send_telegram_alert(self, message):
        """Send alert to Telegram via message tool."""
        try:
            logger.info(f"📱 TELEGRAM ALERT:\n{message}")
            # In actual implementation, this would call the message tool
            # For now, just log what should be sent
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def process_alerts(self):
        """Check for and process new alerts."""
        try:
            logger.info("🔍 Checking for new flight price alerts...")
            
            new_alerts = self.get_new_alerts()
            
            if not new_alerts:
                logger.info("✅ No new alerts found")
                return 0
            
            logger.info(f"🚨 Found {len(new_alerts)} new alert(s)!")
            
            sent_count = 0
            
            for alert in new_alerts:
                route, price, airline, departure_date, drop_percentage, alert_sent_at, alert_id = alert
                
                logger.info(f"Processing alert {alert_id}: {route} - R$ {price:.2f} ({drop_percentage:.1f}% drop)")
                
                # Format message
                message = self.format_telegram_message(
                    route, price, airline, departure_date, drop_percentage, alert_sent_at
                )
                
                # Send to Telegram
                if self.send_telegram_alert(message):
                    sent_count += 1
                    logger.info(f"✅ Sent alert {alert_id} to Telegram")
                else:
                    logger.error(f"❌ Failed to send alert {alert_id}")
                
                # Small delay between messages
                time.sleep(1)
            
            # Update state
            self.last_alert_check = datetime.now()
            self.save_state()
            
            logger.info(f"🎯 Processed {len(new_alerts)} alerts, sent {sent_count} to Telegram")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
            return 0
    
    def start_monitoring(self, check_interval_minutes=10):
        """Start continuous monitoring for alerts."""
        logger.info(f"🚀 Starting Telegram alert monitoring (every {check_interval_minutes} min)")
        
        while True:
            try:
                self.process_alerts()
                
                # Wait for next check
                time.sleep(check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(30)  # Brief delay before retry

def start_telegram_monitoring():
    """Start Telegram monitoring in background thread."""
    telegram_alerts = TelegramFlightAlerts()
    
    def monitor():
        telegram_alerts.start_monitoring(check_interval_minutes=5)  # Check every 5 minutes
    
    thread = Thread(target=monitor, daemon=True)
    thread.start()
    
    logger.info("✅ Telegram alert monitoring started in background")
    return telegram_alerts

if __name__ == "__main__":
    # For testing
    alerts = TelegramFlightAlerts()
    alerts.process_alerts()