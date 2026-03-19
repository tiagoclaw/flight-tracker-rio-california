"""
Email notifications for flight price alerts.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Sends email notifications for flight alerts."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, from_name: str = "Flight Tracker"):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_name = from_name
    
    async def send_email(self, to_email: str, subject: str, message: str, flight=None):
        """Send email notification."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.username}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Create HTML body
            html_body = self._create_html_body(message, flight)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise e
    
    def _create_html_body(self, message: str, flight=None) -> str:
        """Create HTML email body."""
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2E86C1;">🛫 Flight Tracker Alert</h2>
                
                <div style="background: #F8F9FA; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    {message.replace(chr(10), '<br>')}
                </div>
        """
        
        if flight:
            html += f"""
                <div style="border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #28A745; margin-top: 0;">Flight Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold;">Route:</td>
                            <td style="padding: 5px 0;">{flight.departure_airport} → {flight.arrival_airport}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold;">Price:</td>
                            <td style="padding: 5px 0; color: #28A745; font-size: 18px; font-weight: bold;">R$ {flight.price:,.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold;">Dates:</td>
                            <td style="padding: 5px 0;">{flight.departure_date} to {flight.return_date}</td>
                        </tr>
            """
            
            if flight.airline:
                html += f"""
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold;">Airline:</td>
                            <td style="padding: 5px 0;">{flight.airline}</td>
                        </tr>
                """
            
            if flight.booking_url:
                html += f"""
                        <tr>
                            <td style="padding: 5px 0; font-weight: bold;">Book:</td>
                            <td style="padding: 5px 0;"><a href="{flight.booking_url}" style="color: #007BFF;">View Booking Options</a></td>
                        </tr>
                """
            
            html += """
                    </table>
                </div>
            """
        
        html += """
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d;">
                    <p>This is an automated alert from Flight Tracker Rio-California.</p>
                    <p>To manage your alerts, contact: tiago@brazilfinance.com.br</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html