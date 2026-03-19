#!/usr/bin/env python3
"""
Flight Tracker Rio-California
Main entry point for flight price monitoring system.
"""

import asyncio
import argparse
import logging
import os
from datetime import date, datetime, timedelta
from typing import Optional

from tracker import FlightTracker
from tracker.storage.models import CabinClass, AlertType
from tracker.analyzer.trends import PriceAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/flight_tracker.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

async def run_single_check(departure: str, arrival: str, departure_date: str):
    """Run a single price check for specified route and date."""
    
    tracker = FlightTracker()
    
    # Parse date
    target_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
    
    print(f"\n🛫 Checking flights {departure} → {arrival} on {target_date}")
    print("=" * 60)
    
    # Get prices
    flights = await tracker.get_prices(
        departure=departure,
        arrival=arrival,
        departure_date=target_date,
        duration_days=6
    )
    
    if not flights:
        print("❌ No flights found")
        return
    
    # Sort by price
    flights.sort(key=lambda f: f.price)
    
    print(f"✅ Found {len(flights)} flights:")
    print()
    
    for i, flight in enumerate(flights[:10], 1):  # Show top 10
        print(f"{i:2}. R$ {flight.price:>8,.2f} - {flight.airline}")
        print(f"    📅 {flight.departure_date} → {flight.return_date}")
        print(f"    🛫 Stops: {flight.stops} | Duration: {flight.total_duration_minutes//60 if flight.total_duration_minutes else 'N/A'}h")
        print(f"    🔗 Source: {flight.source}")
        if flight.booking_url:
            print(f"    💻 Book: {flight.booking_url[:50]}...")
        print()

async def run_continuous_monitoring():
    """Run continuous price monitoring."""
    
    print("🚀 Starting continuous flight price monitoring...")
    print("Press Ctrl+C to stop")
    print()
    
    tracker = FlightTracker()
    await tracker.run_continuous()

def add_alert(route: str, email: str, alert_type: str, threshold: float, target_price: Optional[float] = None):
    """Add a new price alert."""
    
    tracker = FlightTracker()
    
    alert = tracker.add_price_alert(
        route=route,
        user_email=email,
        alert_type=alert_type,
        threshold_value=threshold,
        target_price=target_price
    )
    
    print(f"✅ Alert created: {alert_type} for {route}")
    print(f"   Email: {email}")
    print(f"   Threshold: {threshold}")
    if target_price:
        print(f"   Target Price: R$ {target_price:.2f}")

def show_price_history(route: str, days: int = 30):
    """Show price history for a route."""
    
    tracker = FlightTracker()
    summary = tracker.get_price_summary(route, days)
    
    print(f"\n📊 Price Summary: {route} (last {days} days)")
    print("=" * 50)
    
    if "message" in summary:
        print(f"❌ {summary['message']}")
        return
    
    print(f"Total flights found: {summary['total_flights']}")
    print(f"Price range: R$ {summary['min_price']:.2f} - R$ {summary['max_price']:.2f}")
    print(f"Average price: R$ {summary['avg_price']:.2f}")
    print(f"Latest price: R$ {summary['latest_price']:.2f} ({summary['latest_date']})")
    print(f"Data sources: {', '.join(summary['sources'])}")

def analyze_trends(route: str):
    """Analyze price trends for a route."""
    
    tracker = FlightTracker()
    analyzer = tracker.analyzer
    
    print(f"\n📈 Price Trends Analysis: {route}")
    print("=" * 40)
    
    # Get trend analysis
    trend_data = analyzer.analyze_trends(route, days=60)
    
    if not trend_data:
        print("❌ No trend data available")
        return
    
    print(f"Trend direction: {trend_data.get('direction', 'Unknown')}")
    print(f"Price change (30 days): {trend_data.get('change_percent', 0):.1f}%")
    print(f"Volatility: {trend_data.get('volatility', 'Unknown')}")
    print(f"Recommendation: {trend_data.get('recommendation', 'No recommendation')}")

def main():
    """Main entry point with argument parsing."""
    
    parser = argparse.ArgumentParser(description='Flight Tracker Rio-California')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check prices for specific route/date')
    check_parser.add_argument('departure', help='Departure airport (GIG, SDU)')
    check_parser.add_argument('arrival', help='Arrival airport (LAX, SFO)')
    check_parser.add_argument('date', help='Departure date (YYYY-MM-DD)')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Start continuous monitoring')
    
    # Alert commands
    alert_parser = subparsers.add_parser('alert', help='Add price alert')
    alert_parser.add_argument('route', help='Route (GIG-LAX, GIG-SFO, etc.)')
    alert_parser.add_argument('email', help='Email for notifications')
    alert_parser.add_argument('type', choices=['price_drop', 'deal_alert', 'target_price'], help='Alert type')
    alert_parser.add_argument('threshold', type=float, help='Threshold value (percentage or price)')
    alert_parser.add_argument('--target-price', type=float, help='Target price (for target_price alerts)')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show price history')
    history_parser.add_argument('route', help='Route (GIG-LAX, GIG-SFO, etc.)')
    history_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    # Trends command
    trends_parser = subparsers.add_parser('trends', help='Analyze price trends')
    trends_parser.add_argument('route', help='Route (GIG-LAX, GIG-SFO, etc.)')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'check':
            asyncio.run(run_single_check(args.departure, args.arrival, args.date))
            
        elif args.command == 'monitor':
            asyncio.run(run_continuous_monitoring())
            
        elif args.command == 'alert':
            add_alert(args.route, args.email, args.type, args.threshold, args.target_price)
            
        elif args.command == 'history':
            show_price_history(args.route, args.days)
            
        elif args.command == 'trends':
            analyze_trends(args.route)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Run main function
    main()