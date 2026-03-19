#!/usr/bin/env python3
"""
Standalone flight monitoring service using ONLY Python built-ins + requests.
Perfect for Railway deployment without external dependencies.
"""

import asyncio
import json
import logging
import os
import sys
import signal
import time
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import hashlib
import random

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class Flight:
    """Simple flight data structure."""
    def __init__(self, departure_airport, arrival_airport, departure_date, return_date, price, airline='Unknown', source='unknown'):
        self.departure_airport = departure_airport
        self.arrival_airport = arrival_airport
        self.departure_date = departure_date
        self.return_date = return_date
        self.price = price
        self.airline = airline
        self.source = source
        self.checked_at = datetime.now()
        self.stops = random.choice([0, 1, 1, 2])  # Realistic distribution

class FlightDB:
    """Simple SQLite database for flights."""
    
    def __init__(self, db_path='data/flights.db'):
        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                departure_airport TEXT NOT NULL,
                arrival_airport TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                return_date TEXT NOT NULL,
                price REAL NOT NULL,
                airline TEXT,
                source TEXT,
                stops INTEGER DEFAULT 1,
                checked_at TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route TEXT NOT NULL,
                price REAL NOT NULL,
                drop_percentage REAL NOT NULL,
                alert_sent_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_flights(self, flights):
        """Save flights to database."""
        conn = sqlite3.connect(self.db_path)
        
        for flight in flights:
            conn.execute('''
                INSERT INTO flights 
                (departure_airport, arrival_airport, departure_date, return_date, price, airline, source, stops, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                flight.departure_airport,
                flight.arrival_airport,
                str(flight.departure_date),
                str(flight.return_date),
                flight.price,
                flight.airline,
                flight.source,
                flight.stops,
                flight.checked_at.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_average_price(self, route, days=30):
        """Get average price for route in last N days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        departure, arrival = route.split('-')
        
        cursor.execute('''
            SELECT AVG(price) FROM flights 
            WHERE departure_airport = ? AND arrival_airport = ? 
            AND checked_at >= ?
        ''', (departure, arrival, since_date))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else None

class SimpleFlightScraper:
    """Standalone flight scraper."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def search_flights(self, departure_airport, arrival_airport, departure_date, return_date):
        """Search flights - generates realistic mock data."""
        
        # Base prices for different routes
        route_prices = {
            'GIG-LAX': 3200, 'GIG-SFO': 3400,
            'SDU-LAX': 3600, 'SDU-SFO': 3800
        }
        
        route = f"{departure_airport}-{arrival_airport}"
        base_price = route_prices.get(route, 3500)
        
        # Airlines for the route
        airlines = ['LATAM Airlines', 'American Airlines', 'United Airlines', 
                   'Delta Air Lines', 'Avianca', 'Copa Airlines']
        
        flights = []
        
        # Generate 8-12 realistic flights
        seed = int(hashlib.md5(f"{departure_date}{route}".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        for i in range(random.randint(8, 12)):
            # Price variation based on realistic factors
            variation = random.uniform(0.75, 1.35)
            
            # Additional variation for advance booking
            days_ahead = (departure_date - date.today()).days
            if days_ahead < 14:
                variation *= 1.2  # More expensive last-minute
            elif days_ahead > 60:
                variation *= 1.1  # Slightly more expensive far ahead
            
            price = round(base_price * variation, 2)
            airline = random.choice(airlines)
            
            flight = Flight(
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                departure_date=departure_date,
                return_date=return_date,
                price=price,
                airline=airline,
                source='realistic_mock'
            )
            
            flights.append(flight)
        
        # Sort by price
        flights.sort(key=lambda f: f.price)
        
        logger.info(f"Generated {len(flights)} flights for {route} on {departure_date}")
        return flights

class AlertManager:
    """Simple alert manager."""
    
    def __init__(self):
        self.db = FlightDB()
    
    def check_price_alerts(self, flights, route):
        """Check if prices trigger alerts."""
        
        if not flights:
            return []
        
        current_min_price = min(f.price for f in flights)
        historical_avg = self.db.get_average_price(route, days=30)
        
        alerts = []
        
        if historical_avg and historical_avg > 0:
            drop_percentage = (historical_avg - current_min_price) / historical_avg
            threshold = float(os.getenv('PRICE_DROP_THRESHOLD', '0.12'))
            
            if drop_percentage >= threshold:
                cheapest = min(flights, key=lambda f: f.price)
                
                alert = {
                    'route': route,
                    'current_price': current_min_price,
                    'historical_avg': historical_avg,
                    'drop_percentage': drop_percentage,
                    'airline': cheapest.airline,
                    'departure_date': cheapest.departure_date
                }
                alerts.append(alert)
                
                logger.info(f"🚨 ALERT: {route} price dropped {drop_percentage*100:.1f}% to R$ {current_min_price:,.2f}")
        
        return alerts
    
    def send_alert(self, alert):
        """Log alert (in production, this would send email/telegram)."""
        
        route = alert['route']
        price = alert['current_price']
        drop = alert['drop_percentage'] * 100
        airline = alert['airline']
        departure = alert['departure_date']
        
        message = f"""
🛫 FLIGHT PRICE ALERT!

✈️  Route: {route}
💰 Price: R$ {price:,.2f} ({airline})
📉 Dropped: {drop:.1f}%
📅 Date: {departure}
🎯 GREAT DEAL - Consider booking!
"""
        
        logger.info(f"📧 ALERT MESSAGE:\n{message}")
        
        # In production, send via email/telegram
        # For now, just log the alert
        return True

class HealthCheckServer:
    """Simple HTTP health check server."""
    
    def __init__(self, port=None):
        # Use Railway's PORT environment variable if available
        self.port = port or int(os.getenv('PORT', '8000'))
        self.server = None
        self.thread = None
        
    def start(self):
        """Start health check server."""
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    if self.path == '/health' or self.path == '/':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        health_data = {
                            'status': 'healthy',
                            'service': 'flight-tracker-rio-california',
                            'timestamp': datetime.now().isoformat(),
                            'routes': ['GIG-LAX', 'GIG-SFO', 'SDU-LAX', 'SDU-SFO'],
                            'port': self.server.server_address[1]
                        }
                        
                        self.wfile.write(json.dumps(health_data, indent=2).encode())
                    else:
                        self.send_response(404)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"error": "Not Found"}')
                except Exception as e:
                    logger.error(f"Health check request failed: {str(e)}")
                    self.send_response(500)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # Log health checks for debugging
                logger.debug(f"Health check: {format % args}")
        
        # Try multiple ports to avoid conflicts
        ports_to_try = [self.port, 8080, 3000, 5000]
        
        for port in ports_to_try:
            try:
                self.server = HTTPServer(('0.0.0.0', port), HealthHandler)
                self.port = port  # Update to actual port used
                
                def run_server():
                    logger.info(f"🏥 Health check server READY on 0.0.0.0:{port}")
                    logger.info(f"📋 Health endpoint: http://0.0.0.0:{port}/health")
                    try:
                        self.server.serve_forever()
                    except Exception as e:
                        logger.error(f"Health server crashed: {str(e)}")
                
                self.thread = threading.Thread(target=run_server, daemon=True)
                self.thread.start()
                
                # Give server time to start
                import time
                time.sleep(1)
                
                # Test the server quickly
                try:
                    import urllib.request
                    urllib.request.urlopen(f'http://localhost:{port}/health', timeout=2)
                    logger.info(f"✅ Health check server verified on port {port}")
                except:
                    logger.warning(f"⚠️  Health check server started but not responding on port {port}")
                
                return True
                
            except OSError as e:
                if "Address already in use" in str(e):
                    logger.warning(f"Port {port} in use, trying next...")
                    continue
                else:
                    logger.error(f"Failed to start health server on port {port}: {str(e)}")
                    continue
            except Exception as e:
                logger.error(f"Unexpected error starting health server on port {port}: {str(e)}")
                continue
        
        logger.error("❌ Could not start health check server on any port")
        return False

class FlightMonitor:
    """Main flight monitoring service."""
    
    def __init__(self):
        self.scraper = SimpleFlightScraper()
        self.db = FlightDB()
        self.alert_manager = AlertManager()
        self.health_server = HealthCheckServer()
        
        # Configuration from environment
        self.check_interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', '3'))
        self.routes = [
            ('GIG', 'LAX', 'Rio Galeão → Los Angeles'),
            ('GIG', 'SFO', 'Rio Galeão → San Francisco'),
            ('SDU', 'LAX', 'Rio Santos Dumont → Los Angeles'),
            ('SDU', 'SFO', 'Rio Santos Dumont → San Francisco')
        ]
        
        logger.info(f"Monitor initialized - {len(self.routes)} routes, check every {self.check_interval_hours}h")
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle."""
        
        cycle_start = datetime.now()
        logger.info("🔄 Starting monitoring cycle...")
        
        total_flights = 0
        total_alerts = 0
        
        for departure, arrival, description in self.routes:
            logger.info(f"🔍 Checking {description}")
            
            try:
                route = f"{departure}-{arrival}"
                
                # Check multiple departure dates (next 60 days, 6-day trips)
                for days_ahead in [15, 30, 45, 60]:
                    dep_date = date.today() + timedelta(days=days_ahead)
                    ret_date = dep_date + timedelta(days=6)
                    
                    flights = self.scraper.search_flights(departure, arrival, dep_date, ret_date)
                    
                    if flights:
                        # Save to database
                        self.db.save_flights(flights)
                        total_flights += len(flights)
                        
                        # Check for alerts
                        alerts = self.alert_manager.check_price_alerts(flights, route)
                        
                        for alert in alerts:
                            self.alert_manager.send_alert(alert)
                            total_alerts += 1
                        
                        # Log best price
                        cheapest = min(flights, key=lambda f: f.price)
                        logger.info(f"   {dep_date}: R$ {cheapest.price:,.2f} ({cheapest.airline}) - {len(flights)} options")
                    
                    # Small delay between date checks
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error checking {description}: {str(e)}")
            
            # Delay between routes
            time.sleep(2)
        
        duration = (datetime.now() - cycle_start).total_seconds()
        logger.info(f"✅ Cycle complete: {total_flights} flights, {total_alerts} alerts ({duration:.1f}s)")
    
    def run_forever(self):
        """Run continuous monitoring."""
        
        # Setup
        logger.info("🛫 FLIGHT MONITOR STARTING - Rio to California")
        logger.info(f"📊 Routes: {len(self.routes)} configured")
        logger.info(f"⏰ Check interval: {self.check_interval_hours} hours")
        logger.info(f"🚨 Alert threshold: {os.getenv('PRICE_DROP_THRESHOLD', '0.12')} drop")
        
        # Start health check server FIRST (Railway needs this immediately)
        logger.info("🏥 Starting health check server...")
        health_started = self.health_server.start()
        
        if health_started:
            logger.info("✅ Health check server ready for Railway")
        else:
            logger.warning("⚠️  Health check server failed to start")
        
        # Give health server time to be ready
        import time
        time.sleep(2)
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                logger.info(f"🎯 Starting cycle #{cycle}")
                
                self.run_monitoring_cycle()
                
                # Wait for next cycle
                wait_seconds = self.check_interval_hours * 3600
                logger.info(f"😴 Sleeping {self.check_interval_hours}h until next cycle...")
                
                time.sleep(wait_seconds)
                
            except KeyboardInterrupt:
                logger.info("👋 Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {str(e)}")
                logger.info("⏳ Waiting 10 minutes before retry...")
                time.sleep(600)

def setup_environment():
    """Setup default environment variables."""
    
    defaults = {
        'CHECK_INTERVAL_HOURS': '3',
        'PRICE_DROP_THRESHOLD': '0.12',
        'DATABASE_URL': 'sqlite:///data/flights.db',
        'LOG_LEVEL': 'INFO'
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value

def main():
    """Main entry point."""
    
    print("🛫 STANDALONE FLIGHT MONITOR - Rio to California")
    print("=" * 60)
    print("📍 4 routes: GIG/SDU → LAX/SFO")
    print("⏰ 24/7 monitoring with smart alerts")
    print("🚨 Price drop detection & notifications")
    print()
    
    # Setup environment first
    setup_environment()
    
    # Start web dashboard server (includes health check)
    print("🌐 Starting web dashboard server...")
    
    try:
        from web_server import start_web_server
        
        # Use Railway PORT or health check port
        dashboard_port = int(os.getenv('PORT', '8000'))
        web_server, web_thread = start_web_server(dashboard_port, 'data/flights.db')
        
        if web_server:
            print("✅ Web dashboard ready - includes health check for Railway")
            print(f"📱 Dashboard available at: http://0.0.0.0:{dashboard_port}")
        else:
            print("⚠️  Web dashboard failed, starting fallback health server...")
            # Fallback to simple health server
            try:
                from simple_health_server import start_health_server
                health_server, health_thread = start_health_server()
            except:
                print("⚠️  All servers failed, continuing with monitoring only...")
            
    except ImportError as e:
        print(f"⚠️  Web server not available: {str(e)}, using simple health check...")
        try:
            from simple_health_server import start_health_server
            health_server, health_thread = start_health_server()
        except:
            print("⚠️  Health server also failed, continuing anyway...")
    except Exception as e:
        print(f"⚠️  Web server error: {str(e)}, using fallback...")
        try:
            from simple_health_server import start_health_server
            health_server, health_thread = start_health_server()
        except:
            print("⚠️  Fallback also failed, continuing anyway...")
    
    # Give servers time to be ready for Railway
    import time
    time.sleep(3)
    
    # Signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        if health_server:
            health_server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start monitoring
    print("🚀 Starting flight monitoring system...")
    monitor = FlightMonitor()
    monitor.run_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Service stopped")
    except Exception as e:
        logger.error(f"💥 Service failed: {str(e)}")
        sys.exit(1)