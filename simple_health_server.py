#!/usr/bin/env python3
"""
Ultra-simple health check server for Railway.
Starts immediately and responds to health checks.
"""

import os
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class SimpleHealthHandler(BaseHTTPRequestHandler):
    """Ultra-simple health check handler."""
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            # Respond to both /health and / (root)
            if self.path in ['/health', '/', '/healthz']:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                # Simple health response
                response = {
                    'status': 'healthy',
                    'service': 'flight-tracker-rio-california',
                    'timestamp': datetime.now().isoformat(),
                    'uptime': time.time()
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            else:
                # 404 for other paths
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Not Found')
                
        except Exception as e:
            # 500 on any error
            print(f"Health check error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Health check failed: {str(e)}'.encode())
    
    def log_message(self, format, *args):
        """Suppress HTTP logs (optional, for cleaner logs)."""
        # Uncomment for debugging:
        # print(f"[{datetime.now()}] {format % args}")
        pass

def start_health_server():
    """Start the health check server."""
    
    # Get port from environment (Railway sets this)
    port = int(os.getenv('PORT', '8000'))
    
    print(f"🏥 Starting health check server on port {port}...")
    
    try:
        server = HTTPServer(('0.0.0.0', port), SimpleHealthHandler)
        
        def run_server():
            print(f"✅ Health check server ready at http://0.0.0.0:{port}/health")
            server.serve_forever()
        
        # Run in daemon thread
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        # Verify server started
        time.sleep(0.5)
        print(f"🎯 Health check endpoint: http://0.0.0.0:{port}/health")
        
        return server, thread
        
    except Exception as e:
        print(f"❌ Failed to start health server: {str(e)}")
        return None, None

if __name__ == "__main__":
    print("🩺 Simple Health Check Server")
    print("=" * 30)
    
    server, thread = start_health_server()
    
    if server:
        try:
            print("🏥 Health server running... (Press Ctrl+C to stop)")
            
            # Keep main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("👋 Shutting down health server...")
            server.shutdown()
    else:
        print("💥 Failed to start health server")
        exit(1)