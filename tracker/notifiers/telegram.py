"""
Telegram notifications for flight price alerts.
"""

import asyncio
import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Sends Telegram notifications for flight alerts."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_telegram(self, chat_id: str, message: str):
        """Send Telegram message."""
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Telegram message sent to {chat_id}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Telegram message: {error_text}")
                        
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            raise e
    
    def format_flight_message(self, message: str, flight=None) -> str:
        """Format message for Telegram with Markdown."""
        
        # Convert basic formatting to Markdown
        formatted_message = message.replace('💰', '💰').replace('🎯', '🎯').replace('🔥', '🔥')
        
        if flight and flight.booking_url:
            formatted_message += f"\n\n[🔗 View Booking Options]({flight.booking_url})"
        
        formatted_message += "\n\n_Flight Tracker Rio-California_"
        
        return formatted_message