"""
Main FlightTracker class for monitoring Rio to California flight prices.
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import os
from dotenv import load_dotenv

from .storage.models import Flight, PriceAlert, DatabaseManager, CabinClass
from .storage.database import DatabaseOperations
from .scrapers.google_flights import GoogleFlightsScraper
from .scrapers.kayak import KayakScraper
from .analyzer.trends import PriceAnalyzer
from .notifiers.email import EmailNotifier
from .notifiers.telegram import TelegramNotifier

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RouteConfig:
    """Configuration for a flight route."""
    
    departure: str  # GIG, SDU
    arrival: str    # LAX, SFO
    duration_days: int = 6
    cabin_class: CabinClass = CabinClass.ECONOMY
    max_stops: int = 2
    enabled: bool = True

@dataclass
class TrackerConfig:
    """Main tracker configuration."""
    
    # Monitoring settings
    check_interval_seconds: int = 3600  # 1 hour
    max_concurrent_requests: int = 5
    request_delay_seconds: int = 2
    
    # Search parameters
    search_window_days: int = 90
    flexible_dates: bool = True
    passengers: int = 1
    
    # Alert settings  
    price_drop_threshold: float = 0.15  # 15%
    deal_threshold: float = 0.80        # 20% below average
    min_price_change_brl: float = 50.0
    
    # Data retention
    keep_price_history_days: int = 365
    
    @classmethod
    def from_env(cls) -> 'TrackerConfig':
        """Create configuration from environment variables."""
        return cls(
            check_interval_seconds=int(os.getenv('PRICE_CHECK_INTERVAL', 3600)),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', 5)),
            request_delay_seconds=int(os.getenv('REQUEST_DELAY', 2)),
            search_window_days=int(os.getenv('SEARCH_WINDOW_DAYS', 90)),
            flexible_dates=os.getenv('FLEXIBLE_DATES', 'true').lower() == 'true',
            passengers=int(os.getenv('PASSENGER_COUNT', 1)),
            price_drop_threshold=float(os.getenv('PRICE_DROP_THRESHOLD', 0.15)),
            deal_threshold=float(os.getenv('DEAL_THRESHOLD', 0.80)),
            min_price_change_brl=float(os.getenv('MIN_PRICE_CHANGE', 50.0)),
            keep_price_history_days=int(os.getenv('KEEP_PRICE_HISTORY_DAYS', 365)),
        )

class FlightTracker:
    """Main flight price tracking system."""
    
    def __init__(self, config: TrackerConfig = None):
        self.config = config or TrackerConfig.from_env()
        
        # Initialize database
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()
        self.db_ops = DatabaseOperations(self.db_manager)
        
        # Initialize scrapers
        self.scrapers = {
            'google_flights': GoogleFlightsScraper(),
            'kayak': KayakScraper(),
        }
        
        # Initialize analyzer
        self.analyzer = PriceAnalyzer(self.db_ops)
        
        # Initialize notifiers
        self.notifiers = []
        self._setup_notifiers()
        
        # Route configurations
        self.routes = self._load_routes()
        
        logger.info(f"FlightTracker initialized with {len(self.routes)} routes")
    
    def _setup_notifiers(self):
        """Setup notification channels."""
        
        # Email notifier
        if all(os.getenv(key) for key in ['EMAIL_USERNAME', 'EMAIL_PASSWORD']):
            email_notifier = EmailNotifier(
                smtp_server=os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
                smtp_port=int(os.getenv('EMAIL_SMTP_PORT', 587)),
                username=os.getenv('EMAIL_USERNAME'),
                password=os.getenv('EMAIL_PASSWORD'),
                from_name=os.getenv('EMAIL_FROM_NAME', 'Flight Tracker'),
            )
            self.notifiers.append(email_notifier)
            logger.info("Email notifier configured")
        
        # Telegram notifier  
        if all(os.getenv(key) for key in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']):
            telegram_notifier = TelegramNotifier(
                bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
                chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            )
            self.notifiers.append(telegram_notifier)
            logger.info("Telegram notifier configured")
    
    def _load_routes(self) -> List[RouteConfig]:
        """Load route configurations."""
        
        # Default routes
        routes = [
            RouteConfig('GIG', 'LAX', duration_days=6, enabled=True),
            RouteConfig('GIG', 'SFO', duration_days=6, enabled=True),
            RouteConfig('SDU', 'LAX', duration_days=6, enabled=False),  # Santos Dumont less common
            RouteConfig('SDU', 'SFO', duration_days=6, enabled=False),
        ]
        
        # Filter enabled routes
        enabled_routes = [r for r in routes if r.enabled]
        
        logger.info(f"Loaded {len(enabled_routes)} enabled routes")
        return enabled_routes
    
    async def get_prices(self, 
                        departure: str, 
                        arrival: str, 
                        departure_date: date,
                        duration_days: int = 6,
                        cabin_class: CabinClass = CabinClass.ECONOMY) -> List[Flight]:
        """Get flight prices for a specific route and date."""
        
        return_date = departure_date + timedelta(days=duration_days)
        
        logger.info(f"Searching flights {departure}-{arrival} "
                   f"{departure_date} to {return_date} ({duration_days} days)")
        
        all_flights = []
        
        # Search across all configured scrapers
        for scraper_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Searching via {scraper_name}...")
                
                flights = await scraper.search_flights(
                    departure_airport=departure,
                    arrival_airport=arrival,
                    departure_date=departure_date,
                    return_date=return_date,
                    cabin_class=cabin_class,
                    passengers=self.config.passengers,
                )
                
                # Add source information
                for flight in flights:
                    flight.source = scraper_name
                    flight.checked_at = datetime.utcnow()
                
                all_flights.extend(flights)
                logger.info(f"Found {len(flights)} flights via {scraper_name}")
                
                # Respect rate limits
                await asyncio.sleep(self.config.request_delay_seconds)
                
            except Exception as e:
                logger.error(f"Error scraping {scraper_name}: {str(e)}")
                continue
        
        # Save flights to database
        if all_flights:
            self.db_ops.save_flights(all_flights)
            logger.info(f"Saved {len(all_flights)} flights to database")
        
        return all_flights
    
    async def monitor_route(self, route: RouteConfig) -> List[Flight]:
        """Monitor prices for a specific route across future dates."""
        
        logger.info(f"Monitoring route {route.departure}-{route.arrival}")
        
        all_flights = []
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=self.config.search_window_days)
        
        # Search multiple departure dates
        current_date = start_date
        while current_date <= end_date:
            
            flights = await self.get_prices(
                departure=route.departure,
                arrival=route.arrival, 
                departure_date=current_date,
                duration_days=route.duration_days,
                cabin_class=route.cabin_class,
            )
            
            all_flights.extend(flights)
            
            # Move to next search date (weekly intervals)
            current_date += timedelta(days=7)
        
        return all_flights
    
    async def check_all_routes(self) -> Dict[str, List[Flight]]:
        """Check prices for all configured routes."""
        
        logger.info(f"Checking prices for {len(self.routes)} routes")
        
        results = {}
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def monitor_single_route(route: RouteConfig):
            async with semaphore:
                route_key = f"{route.departure}-{route.arrival}"
                results[route_key] = await self.monitor_route(route)
        
        # Monitor all routes concurrently
        tasks = [monitor_single_route(route) for route in self.routes]
        await asyncio.gather(*tasks)
        
        # Check for price alerts
        await self.check_price_alerts(results)
        
        return results
    
    async def check_price_alerts(self, new_flights: Dict[str, List[Flight]]):
        """Check if any new flights trigger price alerts."""
        
        logger.info("Checking price alerts...")
        
        # Get all active alerts
        alerts = self.db_ops.get_active_alerts()
        
        for alert in alerts:
            route_flights = new_flights.get(alert.route, [])
            if not route_flights:
                continue
            
            # Find best price for this route
            best_flight = min(route_flights, key=lambda f: f.price)
            
            # Check alert conditions
            should_alert = False
            alert_message = ""
            
            if alert.alert_type == "price_drop":
                # Compare with historical average
                avg_price = self.analyzer.get_average_price(alert.route, days=30)
                if avg_price and best_flight.price < avg_price * (1 - alert.threshold_value):
                    should_alert = True
                    drop_pct = (1 - best_flight.price / avg_price) * 100
                    alert_message = (f"💰 Price Drop Alert!\n"
                                   f"Route: {alert.route}\n"
                                   f"New Price: R$ {best_flight.price:.2f}\n"
                                   f"Drop: {drop_pct:.1f}% below average\n"
                                   f"Departure: {best_flight.departure_date}")
            
            elif alert.alert_type == "target_price":
                if alert.target_price and best_flight.price <= alert.target_price:
                    should_alert = True
                    alert_message = (f"🎯 Target Price Reached!\n"
                                   f"Route: {alert.route}\n" 
                                   f"Price: R$ {best_flight.price:.2f}\n"
                                   f"Target: R$ {alert.target_price:.2f}\n"
                                   f"Departure: {best_flight.departure_date}")
            
            elif alert.alert_type == "deal_alert":
                avg_price = self.analyzer.get_average_price(alert.route, days=60)
                if avg_price and best_flight.price < avg_price * alert.threshold_value:
                    should_alert = True
                    savings = avg_price - best_flight.price
                    alert_message = (f"🔥 Deal Alert!\n"
                                   f"Route: {alert.route}\n"
                                   f"Price: R$ {best_flight.price:.2f}\n"
                                   f"Savings: R$ {savings:.2f}\n"
                                   f"Departure: {best_flight.departure_date}")
            
            # Send alert if conditions met
            if should_alert:
                await self._send_alert(alert, alert_message, best_flight)
    
    async def _send_alert(self, alert: PriceAlert, message: str, flight: Flight):
        """Send price alert to user."""
        
        logger.info(f"Sending alert to {alert.user_email}: {alert.alert_type}")
        
        # Send via all configured notifiers
        for notifier in self.notifiers:
            try:
                if hasattr(notifier, 'send_email') and alert.user_email:
                    await notifier.send_email(
                        to_email=alert.user_email,
                        subject=f"Flight Alert: {alert.route}",
                        message=message,
                        flight=flight,
                    )
                
                if hasattr(notifier, 'send_telegram') and alert.user_telegram_id:
                    await notifier.send_telegram(
                        chat_id=alert.user_telegram_id,
                        message=message,
                    )
                    
            except Exception as e:
                logger.error(f"Failed to send alert via {type(notifier).__name__}: {str(e)}")
        
        # Update alert trigger count
        self.db_ops.update_alert_triggered(alert.id)
    
    def add_price_alert(self,
                       route: str,
                       user_email: str,
                       alert_type: str,
                       threshold_value: float,
                       target_price: float = None,
                       user_telegram_id: str = None) -> PriceAlert:
        """Add a new price alert."""
        
        alert = PriceAlert(
            route=route,
            user_email=user_email,
            user_telegram_id=user_telegram_id,
            alert_type=alert_type,
            threshold_value=threshold_value,
            target_price=target_price,
        )
        
        alert_id = self.db_ops.save_alert(alert)
        logger.info(f"Created alert {alert_id} for {user_email}: {route} {alert_type}")
        
        return alert
    
    async def run_continuous(self):
        """Run continuous price monitoring."""
        
        logger.info("Starting continuous flight price monitoring...")
        
        while True:
            try:
                start_time = datetime.utcnow()
                
                # Check all routes
                results = await self.check_all_routes()
                
                # Log summary
                total_flights = sum(len(flights) for flights in results.values())
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.info(f"Monitoring cycle complete: {total_flights} flights found "
                           f"in {duration:.1f} seconds")
                
                # Wait for next check
                await asyncio.sleep(self.config.check_interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {str(e)}")
                # Wait before retrying
                await asyncio.sleep(60)
    
    def get_price_summary(self, route: str, days: int = 30) -> Dict:
        """Get price summary for a route."""
        
        flights = self.db_ops.get_recent_flights(route, days)
        
        if not flights:
            return {"route": route, "message": "No recent price data"}
        
        prices = [f.price for f in flights]
        
        return {
            "route": route,
            "days": days,
            "total_flights": len(flights),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) / len(prices),
            "latest_price": flights[0].price,  # Most recent
            "latest_date": flights[0].departure_date,
            "sources": list(set(f.source for f in flights)),
        }