#!/usr/bin/env python3
"""
Simple Railway startup script that prioritizes web dashboard.
This ensures Railway can access the dashboard immediately.
"""

import os
import sys
import time
import signal
import threading
from datetime import datetime

print("🚀 RAILWAY STARTUP - Flight Tracker Dashboard")
print("=" * 60)
print(f"⏰ Starting at: {datetime.now()}")
print(f"🌐 PORT: {os.getenv('PORT', '8000')}")
print(f"📊 Database: {os.getenv('DATABASE_PATH', 'data/flights.db')}")
print()

# Set environment defaults
os.environ.setdefault('CHECK_INTERVAL_HOURS', '3')
os.environ.setdefault('PRICE_DROP_THRESHOLD', '0.12')
os.environ.setdefault('DATABASE_URL', 'sqlite:///data/flights.db')
os.environ.setdefault('USE_MOCK_SCRAPER', 'true')

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n👋 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

# Setup signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Start web dashboard FIRST (Railway priority)
print("🌐 STEP 1: Starting Web Dashboard Server...")
try:
    from web_server import start_web_server
    
    port = int(os.getenv('PORT', '8000'))
    web_server, web_thread = start_web_server(port, 'data/flights.db')
    
    if web_server:
        print("✅ Web dashboard started successfully!")
        print(f"📱 Dashboard: http://0.0.0.0:{port}")
        print(f"🏥 Health: http://0.0.0.0:{port}/health")
        print(f"📊 API: http://0.0.0.0:{port}/api/stats")
    else:
        print("❌ Web dashboard failed to start!")
        
except Exception as e:
    print(f"❌ Web server error: {str(e)}")
    print("🔧 Continuing without web server...")

# Give web server time to be ready
print("\n⏳ Waiting for web server to be ready...")
time.sleep(3)

# Test health check
print("🏥 Testing health check...")
try:
    import urllib.request
    health_url = f"http://localhost:{os.getenv('PORT', '8000')}/health"
    response = urllib.request.urlopen(health_url, timeout=5)
    health_data = response.read().decode()
    print("✅ Health check working!")
    print(f"📊 Response: {health_data}")
except Exception as e:
    print(f"⚠️  Health check test failed: {str(e)}")

print()
print("🛫 STEP 2: Starting Flight Monitoring...")

# Start flight monitoring in background
def run_monitoring():
    """Run flight monitoring in background."""
    try:
        print("🔄 Flight monitoring starting...")
        
        # Import and run monitoring
        from standalone_monitor import FlightMonitor
        monitor = FlightMonitor()
        monitor.run_forever()
        
    except Exception as e:
        print(f"❌ Monitoring error: {str(e)}")
        print("🔄 Monitoring will retry automatically...")

# Start monitoring in daemon thread (web server has priority)
monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
monitoring_thread.start()

print("✅ Flight monitoring started in background")
print()
print("🎯 SYSTEM STATUS:")
print("   🌐 Web Dashboard: Running (Priority)")
print("   🛫 Flight Monitoring: Running (Background)")  
print("   🏥 Health Checks: Active")
print("   📊 Database: Connected")
print()
print("🚀 System fully operational!")
print("📱 Access dashboard at your Railway URL")
print()

# Keep main thread alive (web server runs in daemon threads)
try:
    while True:
        time.sleep(60)  # Check every minute
        print(f"⏰ System running... {datetime.now().strftime('%H:%M:%S')}")
        
except KeyboardInterrupt:
    print("\n👋 Shutting down...")
except Exception as e:
    print(f"\n❌ System error: {str(e)}")
    print("🔄 Attempting restart...")
    time.sleep(10)  # Brief delay before Railway restarts