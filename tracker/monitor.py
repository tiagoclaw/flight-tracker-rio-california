#!/usr/bin/env python3
"""
Flight monitoring service for continuous price tracking.
Runs 24/7 checking flight prices and sending alerts.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tracker.scrapers.simple_scraper import SimpleFlightScraper
from tracker.storage.database import FlightDatabase
from tracker.notifiers.email import EmailNotifier
from tracker.notifiers.telegram import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flight_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

class FlightMonitor:
    """24/7 Flight monitoring service."""
    
    def __init__(self):
        self.scraper = SimpleFlightScraper()
        self.db = FlightDatabase()
        self.email_notifier = EmailNotifier()
        self.telegram_notifier = TelegramNotifier()
        
        # Routes to monitor
        self.routes = [
            ('GIG', 'LAX', 'Rio Galeão → Los Angeles'),
            ('GIG', 'SFO', 'Rio Galeão → San Francisco'),
            ('SDU', 'LAX', 'Rio Santos Dumont → Los Angeles'),
            ('SDU', 'SFO', 'Rio Santos Dumont → San Francisco'),
        ]
        
        # Monitoring configuration
        self.check_interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', '6'))
        self.price_drop_threshold = float(os.getenv('PRICE_DROP_THRESHOLD', '0.15'))  # 15%
        
        logger.info(f"Monitor initialized - checking every {self.check_interval_hours}h")
    
    async def check_all_routes(self) -> Dict:
        """Check prices for all configured routes."""
        
        results = {}
        
        for departure, arrival, description in self.routes:
            logger.info(f"🔍 Checking {description}")
            
            try:
                # Check multiple departure dates (next 60 days)
                route_results = []
                
                for days_ahead in [15, 30, 45, 60]:  # 2 weeks to 2 months ahead
                    dep_date = date.today() + timedelta(days=days_ahead)
                    ret_date = dep_date + timedelta(days=6)  # 6-day trips
                    
                    flights = await self.scraper.search_flights(
                        departure_airport=departure,
                        arrival_airport=arrival,
                        departure_date=dep_date,
                        return_date=ret_date
                    )
                    
                    if flights:
                        # Store in database
                        self.db.save_flights(flights)
                        
                        # Get cheapest flight
                        cheapest = min(flights, key=lambda f: f.price)
                        route_results.append({
                            'departure_date': dep_date,
                            'cheapest_price': cheapest.price,
                            'airline': cheapest.airline,
                            'flights_found': len(flights)
                        })
                        
                        logger.info(f"   {dep_date}: R$ {cheapest.price:,.2f} ({cheapest.airline}) - {len(flights)} options")
                    
                    # Delay between searches
                    await asyncio.sleep(2)
                
                results[f"{departure}-{arrival}"] = route_results
                
            except Exception as e:
                logger.error(f"Failed to check {description}: {str(e)}")
                results[f"{departure}-{arrival}"] = []
            
            # Delay between routes
            await asyncio.sleep(5)
        
        return results
    
    async def check_price_alerts(self, results: Dict) -> List[Dict]:
        """Check if any prices triggered alerts."""
        
        alerts = []
        
        for route, route_results in results.items():
            if not route_results:
                continue
                
            departure, arrival = route.split('-')
            
            # Get historical prices for comparison
            historical = self.db.get_historical_prices(departure, arrival, days=30)
            
            if not historical:
                continue  # No historical data yet
                
            avg_historical_price = sum(h['avg_price'] for h in historical) / len(historical)
            
            # Check current prices vs historical
            for result in route_results:
                current_price = result['cheapest_price']
                price_drop = (avg_historical_price - current_price) / avg_historical_price
                
                if price_drop >= self.price_drop_threshold:
                    alerts.append({
                        'type': 'price_drop',
                        'route': route,
                        'departure_date': result['departure_date'],
                        'current_price': current_price,
                        'historical_avg': avg_historical_price,
                        'drop_percentage': price_drop * 100,
                        'airline': result['airline']
                    })
                    
                    logger.info(f"🚨 ALERT: {route} dropped {price_drop*100:.1f}% to R$ {current_price:,.2f}")
        
        return alerts
    
    async def send_alerts(self, alerts: List[Dict]):
        """Send alerts via email and Telegram."""
        
        if not alerts:
            logger.info("No alerts to send")
            return
        
        # Prepare alert message
        message = "🛫 FLIGHT PRICE ALERTS\n\n"
        
        for alert in alerts:
            route = alert['route']
            departure_date = alert['departure_date']
            current_price = alert['current_price']
            drop_pct = alert['drop_percentage']
            airline = alert['airline']
            
            message += f"✈️ {route} on {departure_date}\n"
            message += f"💰 Price: R$ {current_price:,.2f} ({airline})\n"
            message += f"📉 Dropped: {drop_pct:.1f}%\n"
            message += f"🎯 Book now for best deal!\n\n"
        
        # Send via multiple channels
        try:
            await self.email_notifier.send_alert(
                subject="🛫 Flight Price Drop Alert - Rio to California",
                message=message,
                recipient=os.getenv('ALERT_EMAIL', 'user@example.com')
            )
            logger.info(f"✅ Email alert sent")
        except Exception as e:
            logger.error(f"Email alert failed: {str(e)}")
        
        try:
            await self.telegram_notifier.send_message(message)
            logger.info(f"✅ Telegram alert sent")
        except Exception as e:
            logger.error(f"Telegram alert failed: {str(e)}")
    
    async def run_monitoring_cycle(self):
        """Run one complete monitoring cycle."""
        
        logger.info("🚀 Starting monitoring cycle...")
        cycle_start = datetime.now()
        
        try:
            # 1. Check all routes
            results = await self.check_all_routes()
            
            # 2. Check for price alerts
            alerts = await self.check_price_alerts(results)
            
            # 3. Send alerts if any
            await self.send_alerts(alerts)
            
            # 4. Log summary
            total_flights = sum(
                sum(result['flights_found'] for result in route_results)
                for route_results in results.values()
            )
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            logger.info(f"✅ Cycle complete: {total_flights} flights checked, {len(alerts)} alerts sent ({cycle_duration:.1f}s)")
            
        except Exception as e:
            logger.error(f"❌ Monitoring cycle failed: {str(e)}")
    
    async def run_forever(self):
        """Run continuous monitoring."""
        
        logger.info("🌟 Flight Monitor started - Rio to California price tracking")
        logger.info(f"📊 Monitoring {len(self.routes)} routes every {self.check_interval_hours}h")
        logger.info(f"🚨 Alert threshold: {self.price_drop_threshold*100}% price drop")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"🔄 Starting cycle #{cycle_count}")
                
                await self.run_monitoring_cycle()
                
                # Wait before next cycle
                wait_seconds = self.check_interval_hours * 3600
                logger.info(f"😴 Sleeping for {self.check_interval_hours}h until next cycle...")
                
                await asyncio.sleep(wait_seconds)
                
            except KeyboardInterrupt:
                logger.info("👋 Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in monitoring loop: {str(e)}")
                logger.info("⏳ Waiting 10 minutes before retry...")
                await asyncio.sleep(600)  # Wait 10 min on error

async def main():
    """Main entry point."""
    
    # Initialize database
    db = FlightDatabase()
    db.create_tables()
    
    # Start monitoring
    monitor = FlightMonitor()
    await monitor.run_forever()

if __name__ == "__main__":
    asyncio.run(main())