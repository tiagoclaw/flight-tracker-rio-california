"""
Kayak scraper using HTTP requests and HTML parsing.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
import json
import re

import httpx
from bs4 import BeautifulSoup

from ..storage.models import Flight, CabinClass

logger = logging.getLogger(__name__)

class KayakScraper:
    """Kayak flight scraper using HTTP requests."""
    
    def __init__(self):
        self.base_url = "https://www.kayak.com"
        self.session = None
        
        # Headers to mimic real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if not self.session:
            self.session = httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
        return self.session
    
    def _build_search_url(self,
                         departure_airport: str,
                         arrival_airport: str,
                         departure_date: date,
                         return_date: date,
                         cabin_class: CabinClass = CabinClass.ECONOMY,
                         passengers: int = 1) -> str:
        """Build Kayak search URL."""
        
        # Format dates for Kayak (YYYY-MM-DD)
        dep_date = departure_date.strftime('%Y-%m-%d')
        ret_date = return_date.strftime('%Y-%m-%d')
        
        # Map cabin class
        class_mapping = {
            CabinClass.ECONOMY: 'e',
            CabinClass.PREMIUM_ECONOMY: 'p',
            CabinClass.BUSINESS: 'b', 
            CabinClass.FIRST: 'f'
        }
        cabin_code = class_mapping.get(cabin_class, 'e')
        
        # Build search URL
        url = f"{self.base_url}/flights/{departure_airport}-{arrival_airport}/{dep_date}/{ret_date}/{passengers}adults?sort=bestflight_a&fs=cfc={cabin_code}"
        
        return url
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text."""
        try:
            # Remove currency symbols and spaces
            price_clean = re.sub(r'[^\d.,]', '', price_text)
            
            # Handle different price formats
            if 'R$' in price_text or 'BRL' in price_text:
                # Brazilian format: R$ 2.345,50
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                # US format: $2,345.50
                if ',' in price_clean and '.' in price_clean:
                    price_clean = price_clean.replace(',', '')
            
            return float(price_clean)
            
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse price: {price_text}")
            return None
    
    def _parse_duration(self, duration_text: str) -> Optional[int]:
        """Parse flight duration to minutes."""
        try:
            # Extract hours and minutes from formats like "10h 30m" or "10:30"
            if 'h' in duration_text:
                parts = duration_text.lower().replace('h', '').replace('m', '').split()
                hours = int(parts[0]) if len(parts) > 0 else 0
                minutes = int(parts[1]) if len(parts) > 1 else 0
            elif ':' in duration_text:
                hours, minutes = map(int, duration_text.split(':'))
            else:
                # Assume it's just hours
                hours = int(re.search(r'\d+', duration_text).group())
                minutes = 0
            
            return hours * 60 + minutes
            
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse duration: {duration_text}")
            return None
    
    async def search_flights(self,
                           departure_airport: str,
                           arrival_airport: str,
                           departure_date: date,
                           return_date: date,
                           cabin_class: CabinClass = CabinClass.ECONOMY,
                           passengers: int = 1) -> List[Flight]:
        """Search flights on Kayak."""
        
        flights = []
        session = self._get_session()
        
        try:
            # Build search URL
            search_url = self._build_search_url(
                departure_airport, arrival_airport,
                departure_date, return_date,
                cabin_class, passengers
            )
            
            logger.info(f"Searching Kayak: {departure_airport}-{arrival_airport} {departure_date}")
            
            # Make request to Kayak
            response = await session.get(search_url)
            
            if response.status_code != 200:
                logger.warning(f"Kayak returned status {response.status_code}")
                return flights
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find flight results - Kayak uses various classes
            flight_selectors = [
                '.nrc6-inner',
                '.flightcard',
                '.result-item',
                '[data-resultid]',
                '.booking-link'
            ]
            
            flight_elements = []
            for selector in flight_selectors:
                elements = soup.select(selector)
                if elements:
                    flight_elements = elements
                    logger.info(f"Found {len(elements)} flights with selector: {selector}")
                    break
            
            # Alternative: Look for JSON data in script tags
            if not flight_elements:
                flight_data = self._extract_json_data(soup)
                if flight_data:
                    flights.extend(await self._parse_json_flights(
                        flight_data, departure_airport, arrival_airport,
                        departure_date, return_date, cabin_class
                    ))
                    return flights
            
            # Parse HTML flight elements
            for element in flight_elements[:15]:  # Limit results
                try:
                    flight = await self._parse_flight_element(
                        element, departure_airport, arrival_airport,
                        departure_date, return_date, cabin_class
                    )
                    
                    if flight and flight.price > 0:
                        flights.append(flight)
                        logger.debug(f"Parsed Kayak flight: R$ {flight.price:.2f}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse flight element: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(flights)} flights from Kayak")
            
        except Exception as e:
            logger.error(f"Error searching Kayak: {str(e)}")
        
        finally:
            if self.session:
                await self.session.aclose()
                self.session = None
        
        return flights
    
    def _extract_json_data(self, soup: BeautifulSoup) -> Optional[dict]:
        """Extract flight data from JavaScript variables."""
        try:
            # Look for script tags containing flight data
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Look for common Kayak data patterns
                patterns = [
                    r'window\.searchPageJSON\s*=\s*(\{.*?\});',
                    r'window\.resultsList\s*=\s*(\[.*?\]);',
                    r'searchResults\s*:\s*(\{.*?\})',
                    r'"flights"\s*:\s*(\[.*?\])'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script_text, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            if data:
                                logger.info("Found flight data in JSON")
                                return data
                        except json.JSONDecodeError:
                            continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract JSON data: {str(e)}")
            return None
    
    async def _parse_json_flights(self,
                                flight_data: dict,
                                departure_airport: str,
                                arrival_airport: str,
                                departure_date: date,
                                return_date: date,
                                cabin_class: CabinClass) -> List[Flight]:
        """Parse flights from JSON data."""
        flights = []
        
        try:
            # Handle different JSON structures
            if isinstance(flight_data, list):
                results = flight_data
            elif 'flights' in flight_data:
                results = flight_data['flights']
            elif 'results' in flight_data:
                results = flight_data['results']
            else:
                results = []
            
            for item in results[:20]:  # Limit results
                try:
                    price = None
                    airline = "Unknown"
                    stops = 1
                    duration_minutes = None
                    
                    # Extract price
                    if 'price' in item:
                        price = self._parse_price(str(item['price']))
                    elif 'totalPrice' in item:
                        price = self._parse_price(str(item['totalPrice']))
                    
                    # Extract airline
                    if 'airline' in item:
                        airline = item['airline']
                    elif 'carrier' in item:
                        airline = item['carrier']
                    
                    # Extract stops
                    if 'stops' in item:
                        stops = int(item['stops'])
                    
                    # Extract duration
                    if 'duration' in item:
                        duration_minutes = self._parse_duration(str(item['duration']))
                    
                    if price and price > 0:
                        flight = Flight(
                            departure_airport=departure_airport,
                            arrival_airport=arrival_airport,
                            departure_date=departure_date,
                            return_date=return_date,
                            duration_days=(return_date - departure_date).days,
                            price=price,
                            currency='BRL',
                            airline=airline,
                            cabin_class=cabin_class.value,
                            stops=stops,
                            total_duration_minutes=duration_minutes,
                            booking_url=f"{self.base_url}/book",
                            booking_site='kayak',
                            checked_at=datetime.utcnow(),
                            source='kayak',
                            confidence_score=0.7
                        )
                        
                        flights.append(flight)
                
                except Exception as e:
                    logger.warning(f"Failed to parse JSON flight item: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing JSON flights: {str(e)}")
        
        return flights
    
    async def _parse_flight_element(self,
                                  element,
                                  departure_airport: str,
                                  arrival_airport: str,
                                  departure_date: date,
                                  return_date: date,
                                  cabin_class: CabinClass) -> Optional[Flight]:
        """Parse individual flight element from HTML."""
        
        try:
            # Extract price
            price_selectors = ['.price', '.fare-price', '.total-price', '[data-price]']
            price = None
            
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price:
                        break
            
            if not price or price <= 0:
                return None
            
            # Extract airline
            airline_selectors = ['.airline-name', '.carrier', '[data-airline]']
            airline = "Unknown"
            
            for selector in airline_selectors:
                airline_elem = element.select_one(selector)
                if airline_elem:
                    airline = airline_elem.get_text(strip=True)
                    if airline:
                        break
            
            # Extract stops
            stops_selectors = ['.stops-text', '.segments', '.flight-stops']
            stops = 1  # Default assumption
            
            for selector in stops_selectors:
                stops_elem = element.select_one(selector)
                if stops_elem:
                    stops_text = stops_elem.get_text(strip=True).lower()
                    if 'direct' in stops_text or 'nonstop' in stops_text:
                        stops = 0
                    elif '1 stop' in stops_text:
                        stops = 1
                    elif '2 stop' in stops_text:
                        stops = 2
                    break
            
            # Extract duration
            duration_selectors = ['.duration', '.flight-time', '.total-time']
            duration_minutes = None
            
            for selector in duration_selectors:
                duration_elem = element.select_one(selector)
                if duration_elem:
                    duration_text = duration_elem.get_text(strip=True)
                    duration_minutes = self._parse_duration(duration_text)
                    if duration_minutes:
                        break
            
            # Create Flight object
            flight = Flight(
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                departure_date=departure_date,
                return_date=return_date,
                duration_days=(return_date - departure_date).days,
                price=price,
                currency='BRL',
                airline=airline,
                cabin_class=cabin_class.value,
                stops=stops,
                total_duration_minutes=duration_minutes,
                booking_url=f"{self.base_url}/book",
                booking_site='kayak',
                checked_at=datetime.utcnow(),
                source='kayak',
                confidence_score=0.7
            )
            
            return flight
            
        except Exception as e:
            logger.warning(f"Error parsing flight element: {str(e)}")
            return None