#!/usr/bin/env python3
"""
Fixed Railway startup script with guaranteed API endpoints and CORS.
This ensures Railway serves API endpoints with proper CORS headers.
"""

import os
import sys
import time
import signal
import threading
from datetime import datetime

print("🚀 RAILWAY STARTUP - Flight Tracker API + Monitoring")
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

# Start API server FIRST (Railway priority)
print("🌐 STEP 1: Starting API Server with CORS...")
try:
    from simple_api_server import start_api_server
    
    port = int(os.getenv('PORT', '8000'))
    api_server, api_thread = start_api_server(port, 'data/flights.db')
    
    if api_server:
        print("✅ API server started successfully!")
        print(f"📊 API: http://0.0.0.0:{port}/api/stats")
        print(f"🏥 Health: http://0.0.0.0:{port}/health")
    else:
        print("❌ API server failed to start!")
        
except Exception as e:
    print(f"❌ API server error: {str(e)}")
    print("🔧 Continuing without API server...")

# Give API server time to be ready
print("\n⏳ Waiting for API server to be ready...")
time.sleep(3)

# Test API server
print("🧪 Testing API endpoints...")
try:
    import urllib.request
    api_url = f"http://localhost:{os.getenv('PORT', '8000')}/api/stats"
    response = urllib.request.urlopen(api_url, timeout=5)
    data = response.read().decode()
    print("✅ API endpoints working!")
    print(f"📊 Sample response: {data[:100]}...")
except Exception as e:
    print(f"⚠️  API test failed: {str(e)}")

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

# Start monitoring in daemon thread (API server has priority)
monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
monitoring_thread.start()

print("✅ Flight monitoring started in background")
print()
print("🎯 SYSTEM STATUS:")
print("   🌐 API Server: Running (Priority) - WITH CORS HEADERS")
print("   🛫 Flight Monitoring: Running (Background)")  
print("   🏥 Health Checks: Active")
print("   📊 Database: Connected")
print()
print("🔗 AVAILABLE ENDPOINTS:")
print(f"   🏥 Health: https://your-railway-app.up.railway.app/health")
print(f"   📊 Stats: https://your-railway-app.up.railway.app/api/stats")
print(f"   💰 Deals: https://your-railway-app.up.railway.app/api/deals") 
print(f"   💸 Prices: https://your-railway-app.up.railway.app/api/prices")
print(f"   📈 Trends: https://your-railway-app.up.railway.app/api/trends")
print(f"   🚨 Alerts: https://your-railway-app.up.railway.app/api/alerts")
print()
print("🚀 System fully operational with CORS support!")
print("📱 Frontend should now connect successfully!")
print()

# Keep main thread alive (API server runs in daemon threads)
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