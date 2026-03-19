#!/usr/bin/env python3
"""
Simple API Server with CORS for Flight Tracker.
Minimal implementation to serve API endpoints with proper CORS headers.
"""

import os
import json
import sqlite3
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class CORSHandler(BaseHTTPRequestHandler):
    """HTTP handler with CORS support."""
    
    def _send_cors_headers(self):
        """Add CORS headers to response."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '3600')
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS request."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query_params = parse_qs(parsed_path.query)
            
            print(f"[API] GET {path}")
            
            # Health check
            if path == '/health':
                self._serve_health()
            elif path == '/api/stats':
                self._serve_stats()
            elif path == '/api/deals':
                self._serve_deals(query_params)
            elif path == '/api/prices':
                self._serve_prices(query_params)
            elif path == '/api/trends':
                self._serve_trends(query_params)
            elif path == '/api/alerts':
                self._serve_alerts(query_params)
            else:
                self._serve_404()
                
        except Exception as e:
            print(f"[API] Error: {str(e)}")
            self._serve_error(str(e))
    
    def _serve_json(self, data, status_code=200):
        """Send JSON response with CORS headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
    
    def _serve_health(self):
        """Serve health check."""
        health_data = {
            "status": "healthy",
            "service": "flight-tracker-api",
            "timestamp": datetime.now().isoformat(),
            "endpoints": ["/api/stats", "/api/deals", "/api/prices", "/api/trends", "/api/alerts"]
        }
        self._serve_json(health_data)
    
    def _serve_stats(self):
        """Serve database statistics."""
        try:
            db_path = 'data/flights.db'
            if not os.path.exists(db_path):
                # Return mock stats if no database
                stats = {
                    "total_flights": 147,
                    "total_alerts": 0,
                    "routes": {
                        "GIG-LAX": 42,
                        "GIG-SFO": 41,
                        "SDU-LAX": 42,
                        "SDU-SFO": 22
                    },
                    "database_size": 0,
                    "source": "mock_data"
                }
                self._serve_json(stats)
                return
            
            # Get real stats from database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Total flights
            cursor.execute("SELECT COUNT(*) FROM flights")
            total_flights = cursor.fetchone()[0]
            
            # Flights by route
            cursor.execute("SELECT route, COUNT(*) FROM flights GROUP BY route")
            routes = dict(cursor.fetchall())
            
            # Total alerts (if alerts table exists)
            try:
                cursor.execute("SELECT COUNT(*) FROM alerts")
                total_alerts = cursor.fetchone()[0]
            except:
                total_alerts = 0
            
            conn.close()
            
            stats = {
                "total_flights": total_flights,
                "total_alerts": total_alerts,
                "routes": routes,
                "database_size": os.path.getsize(db_path),
                "source": "database"
            }
            
            self._serve_json(stats)
            
        except Exception as e:
            print(f"[API] Stats error: {str(e)}")
            # Fallback to mock data
            stats = {
                "total_flights": 147,
                "total_alerts": 0,
                "routes": {"GIG-LAX": 42, "GIG-SFO": 41, "SDU-LAX": 42, "SDU-SFO": 22},
                "database_size": 0,
                "source": "fallback",
                "error": str(e)
            }
            self._serve_json(stats)
    
    def _serve_deals(self, query_params):
        """Serve best flight deals."""
        limit = int(query_params.get('limit', ['20'])[0])
        
        # Mock deals data
        deals = [
            {
                "route": "GIG-LAX",
                "price": 2444.98,
                "airline": "Avianca",
                "departure_date": "2026-05-18",
                "stops": 2,
                "checked_at": "2026-03-19T10:08:00Z"
            },
            {
                "route": "GIG-SFO",
                "price": 2558.74,
                "airline": "Copa Airlines",
                "departure_date": "2026-05-18",
                "stops": 1,
                "checked_at": "2026-03-19T10:08:00Z"
            },
            {
                "route": "SDU-LAX",
                "price": 2712.29,
                "airline": "Delta Air Lines",
                "departure_date": "2026-05-18",
                "stops": 2,
                "checked_at": "2026-03-19T10:08:00Z"
            },
            {
                "route": "GIG-LAX",
                "price": 2867.09,
                "airline": "LATAM Airlines",
                "departure_date": "2026-04-03",
                "stops": 1,
                "checked_at": "2026-03-19T10:08:00Z"
            },
            {
                "route": "GIG-SFO",
                "price": 2898.65,
                "airline": "American Airlines",
                "departure_date": "2026-04-03",
                "stops": 1,
                "checked_at": "2026-03-19T10:08:00Z"
            },
            {
                "route": "SDU-SFO",
                "price": 3145.96,
                "airline": "United Airlines",
                "departure_date": "2026-04-18",
                "stops": 0,
                "checked_at": "2026-03-19T10:08:00Z"
            }
        ]
        
        self._serve_json(deals[:limit])
    
    def _serve_prices(self, query_params):
        """Serve flight prices."""
        route = query_params.get('route', [None])[0]
        days = int(query_params.get('days', ['7'])[0])
        
        # Mock prices data
        prices = [
            {
                "departure_airport": "GIG",
                "arrival_airport": "LAX",
                "route": "GIG-LAX",
                "departure_date": "2026-05-18",
                "price": 2444.98,
                "airline": "Avianca",
                "stops": 2,
                "checked_at": "2026-03-19T10:08:00Z",
                "source": "realistic_mock"
            },
            {
                "departure_airport": "GIG",
                "arrival_airport": "SFO",
                "route": "GIG-SFO",
                "departure_date": "2026-05-18",
                "price": 2558.74,
                "airline": "Copa Airlines",
                "stops": 1,
                "checked_at": "2026-03-19T10:08:00Z",
                "source": "realistic_mock"
            }
        ]
        
        # Filter by route if specified
        if route:
            prices = [p for p in prices if p['route'] == route]
            
        self._serve_json(prices)
    
    def _serve_trends(self, query_params):
        """Serve price trends."""
        days = int(query_params.get('days', ['30'])[0])
        trends = {}  # Empty for now
        self._serve_json(trends)
    
    def _serve_alerts(self, query_params):
        """Serve price alerts."""
        limit = int(query_params.get('limit', ['50'])[0])
        alerts = []  # Empty for now
        self._serve_json(alerts)
    
    def _serve_404(self):
        """Serve 404 error."""
        self._serve_json({"error": "Not Found", "path": self.path}, 404)
    
    def _serve_error(self, error_msg):
        """Serve 500 error."""
        self._serve_json({"error": "Internal Server Error", "message": error_msg}, 500)

def find_free_port(start_port=8000, max_attempts=10):
    """Find a free port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def start_api_server(port=None, db_path='data/flights.db'):
    """Start the API server."""
    
    if port is None:
        port = int(os.getenv('PORT', '8000'))
    
    # Find free port if specified port is busy
    free_port = find_free_port(port)
    if free_port is None:
        print(f"❌ No free ports found starting from {port}")
        return None, None
    
    if free_port != port:
        print(f"⚠️  Port {port} busy, using port {free_port}")
        port = free_port
    
    try:
        server = HTTPServer(('0.0.0.0', port), CORSHandler)
        
        print(f"🌐 Starting Flight Tracker API Server...")
        print(f"📊 Database: {db_path}")
        print(f"🎯 Port: {port}")
        print(f"🚀 API server started successfully!")
        print(f"🔗 Endpoints available:")
        print(f"   http://0.0.0.0:{port}/health")
        print(f"   http://0.0.0.0:{port}/api/stats")
        print(f"   http://0.0.0.0:{port}/api/deals")
        print(f"   http://0.0.0.0:{port}/api/prices")
        print(f"   http://0.0.0.0:{port}/api/trends")
        print(f"   http://0.0.0.0:{port}/api/alerts")
        print()
        
        # Start server in background thread
        def serve_forever():
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("🛑 API server stopping...")
                server.shutdown()
        
        thread = threading.Thread(target=serve_forever, daemon=True)
        thread.start()
        
        return server, thread
        
    except Exception as e:
        print(f"❌ Failed to start API server: {str(e)}")
        return None, None

if __name__ == "__main__":
    port = int(os.getenv('PORT', '8000'))
    server, thread = start_api_server(port)
    
    if server:
        try:
            # Keep main thread alive
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("👋 Shutting down...")
            server.shutdown()
    else:
        print("❌ Failed to start server")
        exit(1)