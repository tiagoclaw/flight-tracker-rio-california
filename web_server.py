#!/usr/bin/env python3
"""
Web Server for Flight Tracker Dashboard.
Serves both API endpoints and static HTML dashboard.
"""

import os
import json
import sqlite3
import mimetypes
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

from api import FlightDataAPI

class WebServerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for web server and API."""
    
    def __init__(self, *args, api_instance=None, **kwargs):
        self.api = api_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query_params = parse_qs(parsed_path.query)
            
            # CORS headers for API requests
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            # API endpoints
            if path.startswith('/api/'):
                self._handle_api_request(path, query_params)
            
            # Dashboard and static files
            elif path == '/' or path == '/dashboard' or path == '/dashboard/':
                self._serve_dashboard()
            
            elif path == '/dashboard.html':
                self._serve_file('dashboard.html', 'text/html')
            
            # Health check (for Railway)
            elif path == '/health' or path == '/healthz':
                self._send_json_response({'status': 'healthy', 'service': 'flight-tracker-dashboard'})
            
            else:
                self._send_404()
                
        except Exception as e:
            print(f"Error handling request {self.path}: {str(e)}")
            self._send_error_response(500, str(e))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _handle_api_request(self, path, query_params):
        """Handle API requests."""
        
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
        
        else:
            self._send_404()
    
    def _serve_dashboard(self):
        """Serve the main dashboard."""
        self._serve_file('dashboard.html', 'text/html')
    
    def _serve_file(self, filename, content_type=None):
        """Serve a static file."""
        
        try:
            if not os.path.exists(filename):
                self._send_404()
                return
            
            with open(filename, 'rb') as f:
                content = f.read()
            
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or 'text/plain'
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            print(f"Error serving file {filename}: {str(e)}")
            self._send_error_response(500, f"Error serving file: {str(e)}")
    
    def _send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, indent=2).encode())
    
    def _send_404(self):
        """Send 404 response."""
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"error": "Not Found"}')
    
    def _send_error_response(self, status_code, message):
        """Send error response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_response = {'error': message}
        self.wfile.write(json.dumps(error_response).encode())
    
    def log_message(self, format, *args):
        """Log HTTP requests."""
        print(f"[WEB] {format % args}")

def start_web_server(port=8080, db_path='data/flights.db'):
    """Start the web server."""
    
    print(f"🌐 Starting Flight Tracker Web Dashboard...")
    print(f"📊 Database: {db_path}")
    print(f"🎯 Port: {port}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found: {db_path}")
        print("🔧 Dashboard will show empty data until flights are collected")
    
    # Check if dashboard HTML exists
    if not os.path.exists('dashboard.html'):
        print(f"❌ Dashboard HTML not found: dashboard.html")
        return None, None
    
    api = FlightDataAPI(db_path)
    
    def handler(*args, **kwargs):
        return WebServerHandler(*args, api_instance=api, **kwargs)
    
    try:
        server = HTTPServer(('0.0.0.0', port), handler)
        
        def run_server():
            print(f"🚀 Web server started successfully!")
            print(f"📱 Dashboard: http://localhost:{port}")
            print(f"🔗 API endpoints:")
            print(f"   http://localhost:{port}/api/stats")
            print(f"   http://localhost:{port}/api/prices")
            print(f"   http://localhost:{port}/api/trends")
            print(f"   http://localhost:{port}/api/deals")
            print(f"   http://localhost:{port}/api/alerts")
            print(f"🏥 Health check: http://localhost:{port}/health")
            print()
            
            server.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        return server, thread
        
    except Exception as e:
        print(f"❌ Failed to start web server: {str(e)}")
        return None, None

if __name__ == "__main__":
    print("🛫 Flight Tracker Web Dashboard")
    print("=" * 50)
    
    # Use environment PORT or default to 8080
    port = int(os.getenv('PORT', '8080'))
    db_path = os.getenv('DATABASE_PATH', 'data/flights.db')
    
    server, thread = start_web_server(port, db_path)
    
    if server:
        try:
            print("🌐 Web dashboard running... (Press Ctrl+C to stop)")
            
            # Keep main thread alive
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("👋 Shutting down web server...")
            server.shutdown()
    else:
        print("💥 Failed to start web server")
        exit(1)