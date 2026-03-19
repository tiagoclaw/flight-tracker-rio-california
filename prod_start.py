#!/usr/bin/env python3
"""
Production startup script for flight monitoring service.
Handles environment setup and graceful startup.
"""

import asyncio
import logging
import os
import sys
import signal
from pathlib import Path

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flight_monitor.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Setup production environment variables."""
    
    # Default configuration for production
    defaults = {
        'CHECK_INTERVAL_HOURS': '3',  # Check every 3 hours
        'PRICE_DROP_THRESHOLD': '0.12',  # 12% drop trigger
        'DATABASE_URL': 'sqlite:///data/flights.db',
        'USE_MOCK_SCRAPER': 'true',  # Start with mock data
        'LOG_LEVEL': 'INFO',
        'ALERT_EMAIL': 'tiago@example.com',
        'TELEGRAM_CHAT_ID': '540464122'  # Tiago's Telegram ID
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value
            logger.info(f"Set default {key}={value}")

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

async def health_check_server():
    """Simple HTTP server for Railway health checks."""
    
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "healthy", "service": "flight-tracker"}')
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress HTTP logs
        
        server = HTTPServer(('0.0.0.0', 8000), HealthHandler)
        
        def run_server():
            logger.info("🏥 Health check server running on port 8000")
            server.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
    except Exception as e:
        logger.warning(f"Health check server failed to start: {str(e)}")

async def main():
    """Main production startup."""
    
    print("🛫 FLIGHT TRACKER RIO-CALIFORNIA - PRODUCTION")
    print("=" * 50)
    print("📍 Routes: Rio (GIG/SDU) → California (LAX/SFO)")
    print("⏰ Monitoring: 24/7 price tracking")
    print("🚨 Alerts: Email + Telegram")
    print()
    
    # Setup environment
    setup_environment()
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start health check server
    await health_check_server()
    
    # Create data directory
    Path('data').mkdir(exist_ok=True)
    
    try:
        # Import and start monitor
        logger.info("🚀 Starting flight monitoring service...")
        
        # Try to import monitor module
        sys.path.insert(0, '.')
        from tracker.monitor import main as monitor_main
        
        await monitor_main()
        
    except ImportError as e:
        logger.error(f"❌ Failed to import monitor: {str(e)}")
        logger.info("🧪 Running simplified monitoring...")
        
        # Fallback to simple monitoring loop
        await run_simple_monitor()
    
    except Exception as e:
        logger.error(f"❌ Monitor failed: {str(e)}")
        sys.exit(1)

async def run_simple_monitor():
    """Simple monitoring fallback."""
    
    logger.info("🔄 Starting simple monitoring loop...")
    
    cycle = 0
    while True:
        cycle += 1
        logger.info(f"🔍 Monitoring cycle #{cycle}")
        
        try:
            # Simple flight search
            from tracker.scrapers.simple_scraper import SimpleFlightScraper
            from datetime import date, timedelta
            
            scraper = SimpleFlightScraper()
            
            # Check GIG-LAX route
            dep_date = date.today() + timedelta(days=30)
            ret_date = dep_date + timedelta(days=6)
            
            flights = await scraper.search_flights('GIG', 'LAX', dep_date, ret_date)
            
            if flights:
                cheapest = min(flights, key=lambda f: f.price)
                logger.info(f"✅ Found {len(flights)} flights, cheapest: R$ {cheapest.price:,.2f} ({cheapest.airline})")
            else:
                logger.info("⚠️  No flights found")
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
        
        # Wait 3 hours
        logger.info("😴 Sleeping for 3 hours...")
        await asyncio.sleep(3 * 3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Service stopped by user")
    except Exception as e:
        logger.error(f"💥 Service crashed: {str(e)}")
        sys.exit(1)