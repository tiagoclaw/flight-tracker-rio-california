#!/usr/bin/env python3
"""
API Server for Flight Tracker Data Visualization.
Serves flight price data from SQLite to frontend dashboard.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class FlightDataAPI:
    """Flight data API for serving dashboard data."""
    
    def __init__(self, db_path='data/flights.db'):
        self.db_path = db_path
    
    def get_database_stats(self) -> Dict:
        """Get general database statistics."""
        
        if not os.path.exists(self.db_path):
            return {'error': 'Database not found'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Basic stats
            cursor.execute("SELECT COUNT(*) FROM flights")
            total_flights = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM price_alerts")
            total_alerts = cursor.fetchone()[0]
            
            # Date range
            cursor.execute("SELECT MIN(checked_at), MAX(checked_at) FROM flights")
            date_range = cursor.fetchone()
            
            # Routes
            cursor.execute("""
                SELECT departure_airport || '-' || arrival_airport as route, 
                       COUNT(*) as count
                FROM flights 
                GROUP BY departure_airport, arrival_airport 
                ORDER BY count DESC
            """)
            routes = dict(cursor.fetchall())
            
            return {
                'total_flights': total_flights,
                'total_alerts': total_alerts,
                'date_range': {
                    'start': date_range[0],
                    'end': date_range[1]
                },
                'routes': routes,
                'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }
            
        except Exception as e:
            return {'error': str(e)}
        finally:
            conn.close()
    
    def get_route_prices(self, route: str = None, days: int = 7) -> List[Dict]:
        """Get price data for routes."""
        
        if not os.path.exists(self.db_path):
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Date filter
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            if route:
                departure, arrival = route.split('-')
                cursor.execute("""
                    SELECT departure_airport, arrival_airport, departure_date,
                           price, airline, stops, checked_at, source
                    FROM flights 
                    WHERE departure_airport = ? AND arrival_airport = ?
                      AND checked_at >= ?
                    ORDER BY checked_at DESC
                """, (departure, arrival, since_date))
            else:
                cursor.execute("""
                    SELECT departure_airport, arrival_airport, departure_date,
                           price, airline, stops, checked_at, source
                    FROM flights 
                    WHERE checked_at >= ?
                    ORDER BY checked_at DESC
                """, (since_date,))
            
            flights = []
            for row in cursor.fetchall():
                flights.append({
                    'departure_airport': row[0],
                    'arrival_airport': row[1],
                    'route': f"{row[0]}-{row[1]}",
                    'departure_date': row[2],
                    'price': row[3],
                    'airline': row[4],
                    'stops': row[5],
                    'checked_at': row[6],
                    'source': row[7]
                })
            
            return flights
            
        except Exception as e:
            print(f"Error getting route prices: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_price_trends(self, days: int = 30) -> Dict:
        """Get price trends by route."""
        
        if not os.path.exists(self.db_path):
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                SELECT departure_airport || '-' || arrival_airport as route,
                       DATE(checked_at) as date,
                       AVG(price) as avg_price,
                       MIN(price) as min_price,
                       MAX(price) as max_price,
                       COUNT(*) as flight_count
                FROM flights 
                WHERE checked_at >= ?
                GROUP BY route, DATE(checked_at)
                ORDER BY route, date
            """, (since_date,))
            
            trends = {}
            for row in cursor.fetchall():
                route, date, avg_price, min_price, max_price, count = row
                
                if route not in trends:
                    trends[route] = []
                
                trends[route].append({
                    'date': date,
                    'avg_price': round(avg_price, 2),
                    'min_price': min_price,
                    'max_price': max_price,
                    'flight_count': count
                })
            
            return trends
            
        except Exception as e:
            print(f"Error getting price trends: {str(e)}")
            return {}
        finally:
            conn.close()
    
    def get_best_deals(self, limit: int = 20) -> List[Dict]:
        """Get best flight deals (lowest prices)."""
        
        if not os.path.exists(self.db_path):
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT departure_airport, arrival_airport, departure_date,
                       price, airline, stops, checked_at
                FROM flights 
                ORDER BY price ASC
                LIMIT ?
            """, (limit,))
            
            deals = []
            for row in cursor.fetchall():
                deals.append({
                    'route': f"{row[0]}-{row[1]}",
                    'departure_date': row[2],
                    'price': row[3],
                    'airline': row[4],
                    'stops': row[5],
                    'checked_at': row[6]
                })
            
            return deals
            
        except Exception as e:
            print(f"Error getting best deals: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent price alerts."""
        
        if not os.path.exists(self.db_path):
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT route, price, drop_percentage, alert_sent_at
                FROM price_alerts 
                ORDER BY alert_sent_at DESC
                LIMIT ?
            """, (limit,))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'route': row[0],
                    'price': row[1],
                    'drop_percentage': row[2],
                    'alert_sent_at': row[3]
                })
            
            return alerts
            
        except Exception as e:
            print(f"Error getting alerts: {str(e)}")
            return []
        finally:
            conn.close()

class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for flight data API."""
    
    def __init__(self, *args, api_instance=None, **kwargs):
        self.api = api_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query_params = parse_qs(parsed_path.query)
            
            # CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            if path == '/api/stats':
                # Database statistics
                data = self.api.get_database_stats()
                self._send_json_response(data)
                
            elif path == '/api/prices':
                # Flight prices
                route = query_params.get('route', [None])[0]
                days = int(query_params.get('days', [7])[0])
                data = self.api.get_route_prices(route, days)
                self._send_json_response(data)
                
            elif path == '/api/trends':
                # Price trends
                days = int(query_params.get('days', [30])[0])
                data = self.api.get_price_trends(days)
                self._send_json_response(data)
                
            elif path == '/api/deals':
                # Best deals
                limit = int(query_params.get('limit', [20])[0])
                data = self.api.get_best_deals(limit)
                self._send_json_response(data)
                
            elif path == '/api/alerts':
                # Price alerts
                limit = int(query_params.get('limit', [50])[0])
                data = self.api.get_alerts(limit)
                self._send_json_response(data)
                
            elif path == '/':
                # Serve dashboard (will be created)
                self._serve_dashboard()
                
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "Endpoint not found"}')
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, indent=2).encode())
    
    def _serve_dashboard(self):
        """Serve the dashboard HTML."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        # Simple redirect to dashboard
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flight Tracker - Redirecting...</title>
            <meta http-equiv="refresh" content="0; url=/dashboard.html">
        </head>
        <body>
            <p>Redirecting to dashboard...</p>
            <p><a href="/dashboard.html">Click here if not redirected</a></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Log API requests."""
        print(f"[API] {format % args}")

def start_api_server(port=8080, db_path='data/flights.db'):
    """Start the API server."""
    
    api = FlightDataAPI(db_path)
    
    def handler(*args, **kwargs):
        return APIHandler(*args, api_instance=api, **kwargs)
    
    try:
        server = HTTPServer(('0.0.0.0', port), handler)
        
        def run_server():
            print(f"🚀 Flight Data API started on port {port}")
            print(f"📊 Endpoints available:")
            print(f"   GET /api/stats - Database statistics")
            print(f"   GET /api/prices?route=GIG-LAX&days=7 - Flight prices")
            print(f"   GET /api/trends?days=30 - Price trends")
            print(f"   GET /api/deals?limit=20 - Best deals")
            print(f"   GET /api/alerts?limit=50 - Price alerts")
            print(f"   GET / - Dashboard (redirect)")
            print()
            server.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        return server, thread
        
    except Exception as e:
        print(f"❌ Failed to start API server: {str(e)}")
        return None, None

if __name__ == "__main__":
    print("🛫 Flight Tracker Data API")
    print("=" * 40)
    
    server, thread = start_api_server()
    
    if server:
        try:
            print("🌐 API server running... (Press Ctrl+C to stop)")
            
            # Keep main thread alive
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("👋 Shutting down API server...")
            server.shutdown()
    else:
        print("💥 Failed to start API server")
        exit(1)