#!/usr/bin/env python3
"""
Quick test of dashboard functionality locally.
"""

import os
import sys
from datetime import datetime

print("🧪 DASHBOARD TEST")
print("=" * 40)

# Test 1: Check if files exist
files_to_check = [
    'dashboard.html',
    'api.py', 
    'web_server.py',
    'data/flights.db'
]

print("📁 File Check:")
for file in files_to_check:
    exists = os.path.exists(file)
    size = os.path.getsize(file) if exists else 0
    status = "✅" if exists else "❌"
    print(f"   {status} {file}: {size} bytes")

print()

# Test 2: API functionality
print("📡 API Test:")
try:
    sys.path.insert(0, '.')
    from api import FlightDataAPI
    
    api = FlightDataAPI('data/flights.db')
    
    # Test stats
    stats = api.get_database_stats()
    print(f"   ✅ Stats: {stats.get('total_flights', 0)} flights")
    
    # Test deals
    deals = api.get_best_deals(3)
    print(f"   ✅ Deals: {len(deals)} best deals found")
    
    if deals:
        best = deals[0]
        print(f"   💰 Best: {best['route']} - R$ {best['price']:,.2f}")
    
except Exception as e:
    print(f"   ❌ API Error: {str(e)}")

print()

# Test 3: Web server
print("🌐 Web Server Test:")
try:
    from web_server import start_web_server
    
    # Try to start server on test port
    server, thread = start_web_server(port=9999, db_path='data/flights.db')
    
    if server:
        print("   ✅ Web server can start")
        
        # Quick HTTP test
        import time
        time.sleep(1)
        
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:9999/health', timeout=3)
            health_data = response.read().decode()
            print("   ✅ Health check working")
            print(f"   📊 Response: {health_data[:100]}...")
        except Exception as e:
            print(f"   ⚠️  Health check failed: {str(e)}")
        
        # Stop server
        server.shutdown()
    else:
        print("   ❌ Web server failed to start")
        
except Exception as e:
    print(f"   ❌ Web server error: {str(e)}")

print()

# Test 4: Dashboard HTML
print("📄 Dashboard HTML Test:")
try:
    with open('dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for key elements
    checks = [
        ('Chart.js', 'chart.js' in html_content.lower()),
        ('API calls', '/api/' in html_content),
        ('Dashboard title', 'Flight Tracker' in html_content),
        ('Portuguese', 'Voos Monitorados' in html_content)
    ]
    
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        
except Exception as e:
    print(f"   ❌ HTML Error: {str(e)}")

print()
print("🎯 RECOMMENDATIONS:")

# Check data
if os.path.exists('data/flights.db'):
    size = os.path.getsize('data/flights.db')
    if size > 1000:
        print("   ✅ Database has data - dashboard should work")
    else:
        print("   ⚠️  Database small - may need more data collection")
else:
    print("   ❌ No database - run monitoring first")

print("   🚀 To test locally: python3 web_server.py")
print("   🌐 Then open: http://localhost:8080")

print()
print(f"⏰ Test completed at {datetime.now()}")