#!/usr/bin/env python3
"""
Flight Alert Notifier for Telegram.
Monitors for new flight price alerts and sends notifications.
"""

import os
import json
import sqlite3
import time
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] alert_notifier: %(message)s'
)
logger = logging.getLogger(__name__)

class AlertNotifier:
    """Monitors flight alerts and sends Telegram notifications."""
    
    def __init__(self, db_path='data/flights.db', state_file='alert_notifier_state.json'):
        self.db_path = db_path
        self.state_file = state_file
        self.telegram_chat_id = '540464122'  # Tiago's chat ID
        self.last_check = self.load_last_check()
        
    def load_last_check(self):
        """Load last check timestamp from state file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    return datetime.fromisoformat(state.get('last_check', '2026-03-19T00:00:00'))
            return datetime.now() - timedelta(hours=1)  # Check last hour on first run
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
            return datetime.now() - timedelta(hours=1)
    
    def save_last_check(self):
        """Save last check timestamp to state file."""
        try:
            state = {
                'last_check': self.last_check.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def get_new_alerts(self):
        """Get new flight alerts since last check."""
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"Database not found: {self.db_path}")
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if alerts table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
            if not cursor.fetchone():
                logger.info("Alerts table does not exist yet")
                conn.close()
                return []
            
            # Get alerts since last check
            cursor.execute("""
                SELECT route, price, airline, departure_date, drop_percentage, alert_sent_at
                FROM alerts 
                WHERE alert_sent_at > ?
                ORDER BY alert_sent_at DESC
            """, (self.last_check.isoformat(),))
            
            alerts = cursor.fetchall()
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting new alerts: {e}")
            return []
    
    def format_alert_message(self, route, price, airline, departure_date, drop_percentage, alert_sent_at):
        """Format alert for Telegram message."""
        
        route_names = {
            'GIG-LAX': '🛫 Rio Galeão → Los Angeles',
            'GIG-SFO': '🛫 Rio Galeão → San Francisco', 
            'SDU-LAX': '🛫 Santos Dumont → Los Angeles',
            'SDU-SFO': '🛫 Santos Dumont → San Francisco'
        }
        
        route_display = route_names.get(route, f'🛫 {route}')
        
        # Format departure date
        try:
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            dep_date = departure_date
        
        message = f"""🚨 **ALERTA DE PREÇO - VOOS RIO → CALIFORNIA!**

{route_display}
💰 **Preço:** R$ {price:,.2f}
✈️  **Companhia:** {airline}
📅 **Partida:** {dep_date}
📉 **Queda:** {drop_percentage:.1f}%

🎯 **ÓTIMA OPORTUNIDADE!** Considere reservar!

⏰ Detectado em: {alert_sent_at}"""

        return message
    
    async def send_telegram_alert(self, message):
        """Send alert via Telegram using message tool."""
        try:
            # Use the message tool to send to Telegram
            # This is handled by the parent process that has access to tools
            return {
                'action': 'send_telegram',
                'chat_id': self.telegram_chat_id,
                'message': message
            }
        except Exception as e:
            logger.error(f"Error preparing Telegram message: {e}")
            return None
    
    def check_for_alerts(self):
        """Check for new alerts and send notifications."""
        logger.info("🔍 Checking for new flight price alerts...")
        
        try:
            new_alerts = self.get_new_alerts()
            
            if not new_alerts:
                logger.info("No new alerts found")
                return []
            
            logger.info(f"Found {len(new_alerts)} new alert(s)")
            
            telegram_messages = []
            
            for alert in new_alerts:
                route, price, airline, departure_date, drop_percentage, alert_sent_at = alert
                
                logger.info(f"🚨 New alert: {route} - R$ {price:.2f} ({drop_percentage:.1f}% drop)")
                
                # Format message for Telegram
                message = self.format_alert_message(
                    route, price, airline, departure_date, drop_percentage, alert_sent_at
                )
                
                # Prepare for sending
                telegram_msg = self.send_telegram_alert(message)
                if telegram_msg:
                    telegram_messages.append(telegram_msg)
            
            # Update last check time
            self.last_check = datetime.now()
            self.save_last_check()
            
            return telegram_messages
            
        except Exception as e:
            logger.error(f"Error checking for alerts: {e}")
            return []

def main():
    """Main function for testing."""
    notifier = AlertNotifier()
    messages = notifier.check_for_alerts()
    
    if messages:
        print(f"Would send {len(messages)} Telegram message(s)")
        for msg in messages:
            print("---")
            print(msg['message'])
    else:
        print("No new alerts to send")

if __name__ == "__main__":
    main()