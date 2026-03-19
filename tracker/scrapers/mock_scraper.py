"""
Mock flight data scraper for testing and development.
Generates realistic flight data for Rio-California routes.
"""

import asyncio
import logging
import random
from datetime import date, datetime, timedelta
from typing import List

from ..storage.models import Flight, CabinClass

logger = logging.getLogger(__name__)

class MockFlightScraper:
    """Mock scraper that generates realistic flight data for testing."""
    
    def __init__(self):
        # Realistic airlines for GIG/SDU -> LAX/SFO routes
        self.airlines = [
            "American Airlines",
            "Delta Air Lines", 
            "United Airlines",
            "LATAM Airlines",
            "Avianca",
            "Copa Airlines",
            "Azul Brazilian Airlines",
            "GOL Linhas Aéreas",
            "Air France",
            "KLM",
            "Lufthansa"
        ]
        
        # Base prices for different routes (in BRL)
        self.base_prices = {
            "GIG-LAX": 3200,
            "GIG-SFO": 3400,
            "SDU-LAX": 3500,  # Santos Dumont typically more expensive
            "SDU-SFO": 3700,
        }
        
        # Seasonal multipliers
        self.seasonal_factors = {
            12: 1.4,  # December (Christmas)
            1: 1.3,   # January (New Year)
            2: 1.2,   # February (Carnival season)
            6: 1.15,  # June (Brazil winter vacation)
            7: 1.25,  # July (US summer + Brazil vacation)
            8: 1.2,   # August (continued vacation season)
            11: 1.1,  # November (Thanksgiving approach)
        }
        
        # Price variation factors
        self.variation_factors = [
            0.7,   # Excellent deals (30% off)
            0.8,   # Good deals (20% off) 
            0.85,  # Fair deals (15% off)
            0.9,   # Small discounts (10% off)
            1.0,   # Base price
            1.0,   # Base price
            1.0,   # Base price
            1.1,   # Slightly expensive (10% more)
            1.15,  # More expensive (15% more)
            1.2,   # Expensive (20% more)
            1.3,   # Very expensive (30% more)
        ]
    
    async def search_flights(self,
                           departure_airport: str,
                           arrival_airport: str,
                           departure_date: date,
                           return_date: date,
                           cabin_class: CabinClass = CabinClass.ECONOMY,
                           passengers: int = 1) -> List[Flight]:
        """Generate mock flight data."""
        
        route = f"{departure_airport}-{arrival_airport}"
        
        logger.info(f"Generating mock flights: {route} {departure_date}")
        
        # Simulate network delay
        await asyncio.sleep(random.uniform(1, 3))
        
        flights = []
        
        # Generate 5-15 random flights
        num_flights = random.randint(5, 15)
        
        for i in range(num_flights):
            flight = self._generate_flight(
                departure_airport, arrival_airport,
                departure_date, return_date, cabin_class
            )
            flights.append(flight)
        
        # Sort by price (cheapest first)
        flights.sort(key=lambda f: f.price)
        
        logger.info(f"Generated {len(flights)} mock flights")
        
        return flights
    
    def _generate_flight(self,
                        departure_airport: str,
                        arrival_airport: str,
                        departure_date: date,
                        return_date: date,
                        cabin_class: CabinClass) -> Flight:
        """Generate a single realistic flight."""
        
        route = f"{departure_airport}-{arrival_airport}"
        
        # Base price for route
        base_price = self.base_prices.get(route, 3500)
        
        # Apply cabin class multiplier
        cabin_multipliers = {
            CabinClass.ECONOMY: 1.0,
            CabinClass.PREMIUM_ECONOMY: 1.5,
            CabinClass.BUSINESS: 2.8,
            CabinClass.FIRST: 4.2
        }
        base_price *= cabin_multipliers.get(cabin_class, 1.0)
        
        # Apply seasonal factor
        month = departure_date.month
        seasonal_factor = self.seasonal_factors.get(month, 1.0)
        base_price *= seasonal_factor
        
        # Apply random price variation
        variation = random.choice(self.variation_factors)
        final_price = base_price * variation
        
        # Add small random noise
        noise = random.uniform(0.95, 1.05)
        final_price *= noise
        
        # Round to realistic price (multiples of 10)
        final_price = round(final_price / 10) * 10
        
        # Generate flight details
        airline = random.choice(self.airlines)
        
        # Stops (most flights have 1+ stops for GIG/SDU -> LAX/SFO)
        stops_weights = [0.1, 0.6, 0.25, 0.05]  # 0, 1, 2, 3+ stops
        stops = random.choices([0, 1, 2, 3], weights=stops_weights)[0]
        
        # Duration (longer for more stops)
        base_duration = {
            0: random.randint(11*60, 13*60),  # Direct: 11-13h
            1: random.randint(14*60, 18*60),  # 1 stop: 14-18h  
            2: random.randint(18*60, 24*60),  # 2 stops: 18-24h
            3: random.randint(24*60, 30*60),  # 3+ stops: 24-30h
        }
        duration_minutes = base_duration.get(stops, 16*60)
        
        # Booking URL (simulate different booking sites)
        booking_sites = ['kayak.com', 'expedia.com', 'decolar.com', 'submarinoviagens.com.br']
        booking_site = random.choice(booking_sites)
        booking_url = f"https://{booking_site}/flights/book/{route.lower()}"
        
        # Seats available (simulate availability)
        seats_available = random.randint(1, 9) if random.random() < 0.8 else None
        
        # Confidence score (mock data is reliable for testing)
        confidence_score = random.uniform(0.85, 0.95)
        
        flight = Flight(
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_date=departure_date,
            return_date=return_date,
            duration_days=(return_date - departure_date).days,
            price=final_price,
            currency='BRL',
            airline=airline,
            flight_number=self._generate_flight_number(airline),
            cabin_class=cabin_class.value,
            stops=stops,
            total_duration_minutes=duration_minutes,
            booking_url=booking_url,
            booking_site=booking_site.split('.')[0],
            seats_available=seats_available,
            checked_at=datetime.utcnow(),
            source='mock_scraper',
            is_cached=False,
            confidence_score=confidence_score
        )
        
        return flight
    
    def _generate_flight_number(self, airline: str) -> str:
        """Generate realistic flight number."""
        
        # Airline code mapping
        codes = {
            "American Airlines": "AA",
            "Delta Air Lines": "DL",
            "United Airlines": "UA", 
            "LATAM Airlines": "LA",
            "Avianca": "AV",
            "Copa Airlines": "CM",
            "Azul Brazilian Airlines": "AD",
            "GOL Linhas Aéreas": "G3",
            "Air France": "AF",
            "KLM": "KL",
            "Lufthansa": "LH"
        }
        
        code = codes.get(airline, "XX")
        number = random.randint(100, 9999)
        
        return f"{code}{number}"
    
    def get_price_history(self, route: str, days: int = 30) -> List[dict]:
        """Generate mock price history for testing trend analysis."""
        
        history = []
        base_price = self.base_prices.get(route, 3500)
        
        # Generate daily prices with realistic trends
        for i in range(days):
            date_point = datetime.utcnow() - timedelta(days=days-i)
            
            # Simulate price trends (weekly cycles + random walks)
            week_cycle = 0.1 * random.sin(2 * 3.14159 * i / 7)  # Weekly pattern
            trend = 0.02 * (i - days/2) / days  # Slight overall trend
            noise = random.uniform(-0.15, 0.15)  # Random daily variation
            
            price_factor = 1 + week_cycle + trend + noise
            price = base_price * max(0.7, min(1.3, price_factor))  # Clamp to reasonable range
            
            history.append({
                'date': date_point.date(),
                'price': round(price, 2),
                'route': route
            })
        
        return history