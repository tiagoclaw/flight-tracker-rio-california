#!/usr/bin/env python3
"""
Test script for flight scrapers.
"""

import asyncio
import os
import sys
from datetime import date, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from tracker.scrapers.mock_scraper import MockFlightScraper
from tracker.scrapers.google_flights import GoogleFlightsScraper
from tracker.scrapers.kayak import KayakScraper
from tracker.storage.models import CabinClass

async def test_mock_scraper():
    """Test mock scraper."""
    print("🧪 Testing Mock Scraper...")
    
    scraper = MockFlightScraper()
    
    # Test GIG -> LAX
    departure_date = date.today() + timedelta(days=30)
    return_date = departure_date + timedelta(days=6)
    
    flights = await scraper.search_flights(
        departure_airport='GIG',
        arrival_airport='LAX',
        departure_date=departure_date,
        return_date=return_date,
        cabin_class=CabinClass.ECONOMY
    )
    
    print(f"✅ Mock scraper found {len(flights)} flights")
    
    if flights:
        print("\n📊 Sample flights:")
        for i, flight in enumerate(flights[:5], 1):
            print(f"{i}. R$ {flight.price:>8,.2f} - {flight.airline}")
            print(f"   🛫 {flight.departure_date} → {flight.return_date}")
            print(f"   ⏱️  {flight.total_duration_minutes//60 if flight.total_duration_minutes else 'N/A'}h | Stops: {flight.stops}")
            print()
    
    return len(flights) > 0

async def test_google_flights_scraper():
    """Test Google Flights scraper (requires Chrome)."""
    print("\n🌐 Testing Google Flights Scraper...")
    
    try:
        scraper = GoogleFlightsScraper(headless=True)
        
        departure_date = date.today() + timedelta(days=45)
        return_date = departure_date + timedelta(days=6)
        
        flights = await scraper.search_flights(
            departure_airport='GIG',
            arrival_airport='LAX',
            departure_date=departure_date,
            return_date=return_date,
            cabin_class=CabinClass.ECONOMY
        )
        
        scraper.close()
        
        print(f"✅ Google Flights found {len(flights)} flights")
        
        if flights:
            print("\n📊 Sample flights:")
            for i, flight in enumerate(flights[:3], 1):
                print(f"{i}. R$ {flight.price:>8,.2f} - {flight.airline}")
                print(f"   🛫 {flight.departure_date} → {flight.return_date}")
                print()
        
        return len(flights) > 0
        
    except Exception as e:
        print(f"❌ Google Flights error: {str(e)}")
        print("   (This is normal if Chrome/ChromeDriver is not installed)")
        return False

async def test_kayak_scraper():
    """Test Kayak scraper."""
    print("\n🏄‍♂️ Testing Kayak Scraper...")
    
    try:
        scraper = KayakScraper()
        
        departure_date = date.today() + timedelta(days=45)
        return_date = departure_date + timedelta(days=6)
        
        flights = await scraper.search_flights(
            departure_airport='GIG',
            arrival_airport='SFO',
            departure_date=departure_date,
            return_date=return_date,
            cabin_class=CabinClass.ECONOMY
        )
        
        print(f"✅ Kayak found {len(flights)} flights")
        
        if flights:
            print("\n📊 Sample flights:")
            for i, flight in enumerate(flights[:3], 1):
                print(f"{i}. R$ {flight.price:>8,.2f} - {flight.airline}")
                print(f"   🛫 {flight.departure_date} → {flight.return_date}")
                print()
        
        return len(flights) > 0
        
    except Exception as e:
        print(f"❌ Kayak error: {str(e)}")
        return False

async def main():
    """Run all scraper tests."""
    print("🛫 Flight Tracker Rio-California - Scraper Tests")
    print("=" * 60)
    
    results = {}
    
    # Test mock scraper (should always work)
    results['mock'] = await test_mock_scraper()
    
    # Test real scrapers
    results['google_flights'] = await test_google_flights_scraper()
    results['kayak'] = await test_kayak_scraper()
    
    # Summary
    print("\n🎯 Test Results Summary:")
    print("-" * 30)
    
    for scraper, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{scraper:<15}: {status}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    if results['mock']:
        print("✅ Mock scraper works - good for development/testing")
    
    if results['google_flights']:
        print("✅ Google Flights works - primary scraper ready")
    elif not results['google_flights']:
        print("⚠️  Google Flights failed - install Chrome/ChromeDriver for production")
    
    if results['kayak']:
        print("✅ Kayak works - good backup scraper")
    elif not results['kayak']:
        print("⚠️  Kayak failed - may have anti-bot protection")
    
    # Next steps
    print("\n🚀 Next Steps:")
    
    if any(results.values()):
        print("1. ✅ At least one scraper is working")
        print("2. 🗄️  Test database integration: python -c \"from tracker import FlightTracker; print('DB OK')\"")
        print("3. 📊 Test full pipeline: python main.py check GIG LAX 2026-04-15")
        print("4. ⏰ Test monitoring: python main.py monitor (Ctrl+C to stop)")
    else:
        print("1. ❌ All scrapers failed - check dependencies")
        print("2. 📦 Install Chrome: apt-get install google-chrome-stable")
        print("3. 📦 Install requirements: pip install -r requirements.txt")
        print("4. 🧪 Use mock mode: USE_MOCK_SCRAPER=true python main.py check GIG LAX 2026-04-15")

if __name__ == "__main__":
    asyncio.run(main())