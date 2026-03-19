"""
Google Flights scraper using Selenium WebDriver.
"""

import asyncio
import logging
from datetime import date, datetime
from typing import List, Optional
from dataclasses import dataclass
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from ..storage.models import Flight, CabinClass

logger = logging.getLogger(__name__)

@dataclass
class FlightResult:
    """Individual flight search result."""
    price: float
    currency: str
    airline: str
    departure_time: str
    arrival_time: str
    duration: str
    stops: int
    booking_url: str

class GoogleFlightsScraper:
    """Google Flights scraper using Selenium."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def _setup_driver(self):
        """Setup Chrome WebDriver."""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
                
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Disable images and CSS for faster loading
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=chrome_options
            )
            
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("Chrome WebDriver initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            raise e
    
    def _build_search_url(self, 
                         departure_airport: str,
                         arrival_airport: str, 
                         departure_date: date,
                         return_date: date,
                         cabin_class: CabinClass = CabinClass.ECONOMY,
                         passengers: int = 1) -> str:
        """Build Google Flights search URL."""
        
        # Format dates for Google Flights (YYYY-MM-DD)
        dep_date = departure_date.strftime('%Y-%m-%d')
        ret_date = return_date.strftime('%Y-%m-%d')
        
        # Map cabin class
        class_mapping = {
            CabinClass.ECONOMY: '1',
            CabinClass.PREMIUM_ECONOMY: '2', 
            CabinClass.BUSINESS: '3',
            CabinClass.FIRST: '4'
        }
        cabin_code = class_mapping.get(cabin_class, '1')
        
        # Build URL
        base_url = "https://www.google.com/travel/flights"
        url = (f"{base_url}?"
               f"f=0"  # Round trip
               f"&gl=BR"  # Country: Brazil
               f"&hl=pt"  # Language: Portuguese
               f"&curr=BRL"  # Currency: Brazilian Real
               f"&tfs=CAEQAhoeag0IAxIJL20vMDJqNWN6EgoyMDI2LTAzLTE5mgEPCAESDQgDEgkvbS8wMmpfdGpyAggBmgEPCAESDQgDEgkvbS8wMmpfdGo"
               f"&iti=")
        
        # Flight details
        url += (f"{departure_airport}_{arrival_airport}_"
                f"{dep_date}*{arrival_airport}_{departure_airport}_"
                f"{ret_date}_{passengers}_{cabin_code}_0__")
        
        return url
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text like 'R$ 2.345' or '$2,345'."""
        try:
            # Remove currency symbols and extract numbers
            price_clean = re.sub(r'[^\d.,]', '', price_text)
            price_clean = price_clean.replace('.', '').replace(',', '.')
            
            # Handle Brazilian format (R$ 2.345,50)
            if ',' in price_clean and len(price_clean.split(',')[-1]) == 2:
                price_clean = price_clean.replace(',', '.')
            # Handle US format ($2,345.50) 
            elif ',' in price_clean and len(price_clean.split('.')[-1]) == 2:
                price_clean = price_clean.replace(',', '')
                
            return float(price_clean)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse price '{price_text}': {str(e)}")
            return None
    
    def _parse_duration(self, duration_text: str) -> Optional[int]:
        """Parse duration like '10h 30m' to minutes."""
        try:
            duration_text = duration_text.lower()
            hours = 0
            minutes = 0
            
            # Extract hours
            hour_match = re.search(r'(\d+)h', duration_text)
            if hour_match:
                hours = int(hour_match.group(1))
            
            # Extract minutes
            min_match = re.search(r'(\d+)m', duration_text)
            if min_match:
                minutes = int(min_match.group(1))
            
            return hours * 60 + minutes
            
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse duration '{duration_text}'")
            return None
    
    def _parse_stops(self, stops_text: str) -> int:
        """Parse number of stops."""
        stops_text = stops_text.lower()
        
        if 'direto' in stops_text or 'direct' in stops_text or 'nonstop' in stops_text:
            return 0
        elif '1 parada' in stops_text or '1 stop' in stops_text:
            return 1
        elif '2 parada' in stops_text or '2 stop' in stops_text:
            return 2
        else:
            # Try to extract number
            match = re.search(r'(\d+)', stops_text)
            return int(match.group(1)) if match else 1
    
    async def search_flights(self,
                           departure_airport: str,
                           arrival_airport: str,
                           departure_date: date,
                           return_date: date,
                           cabin_class: CabinClass = CabinClass.ECONOMY,
                           passengers: int = 1) -> List[Flight]:
        """Search flights on Google Flights."""
        
        if not self.driver:
            self._setup_driver()
        
        flights = []
        
        try:
            # Build search URL
            search_url = self._build_search_url(
                departure_airport, arrival_airport,
                departure_date, return_date,
                cabin_class, passengers
            )
            
            logger.info(f"Searching Google Flights: {departure_airport}-{arrival_airport} {departure_date}")
            
            # Navigate to search
            self.driver.get(search_url)
            
            # Wait for results to load
            await asyncio.sleep(5)
            
            # Try different selectors for flight results
            flight_selectors = [
                '[data-test-id="flight-card"]',
                '.pIav2d',  # Common Google Flights result class
                '[role="listitem"]',
                '.yR1fYc'
            ]
            
            flight_elements = []
            for selector in flight_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        flight_elements = elements
                        logger.info(f"Found {len(elements)} flight elements with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not flight_elements:
                logger.warning("No flight elements found on page")
                return flights
            
            # Parse each flight result
            for i, element in enumerate(flight_elements[:20]):  # Limit to 20 results
                try:
                    flight_data = await self._parse_flight_element(element)
                    
                    if flight_data and flight_data.price > 0:
                        # Create Flight object
                        flight = Flight(
                            departure_airport=departure_airport,
                            arrival_airport=arrival_airport,
                            departure_date=departure_date,
                            return_date=return_date,
                            duration_days=(return_date - departure_date).days,
                            price=flight_data.price,
                            currency=flight_data.currency,
                            airline=flight_data.airline,
                            cabin_class=cabin_class.value,
                            stops=flight_data.stops,
                            total_duration_minutes=self._parse_duration(flight_data.duration),
                            booking_url=flight_data.booking_url,
                            booking_site='google_flights',
                            checked_at=datetime.utcnow(),
                            source='google_flights',
                            confidence_score=0.8  # Google Flights is reliable
                        )
                        
                        flights.append(flight)
                        logger.debug(f"Parsed flight: R$ {flight.price:.2f} via {flight.airline}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse flight element {i}: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(flights)} flights from Google Flights")
            
        except Exception as e:
            logger.error(f"Error searching Google Flights: {str(e)}")
            
        return flights
    
    async def _parse_flight_element(self, element) -> Optional[FlightResult]:
        """Parse individual flight element."""
        try:
            # Try to extract price
            price_selectors = ['[data-test-id="price"]', '.YMlIz', '.U3gSDe', '[data-test-id="trip-price"]']
            price_text = None
            
            for selector in price_selectors:
                try:
                    price_elem = element.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text:
                        break
                except NoSuchElementException:
                    continue
            
            if not price_text:
                return None
            
            price = self._parse_price(price_text)
            if not price:
                return None
            
            # Try to extract airline
            airline_selectors = ['[data-test-id="airline"]', '.Ir0Voe', '.sSHqwe']
            airline = "Unknown"
            
            for selector in airline_selectors:
                try:
                    airline_elem = element.find_element(By.CSS_SELECTOR, selector)
                    airline = airline_elem.text.strip()
                    if airline:
                        break
                except NoSuchElementException:
                    continue
            
            # Try to extract stops info
            stops_selectors = ['[data-test-id="stops"]', '.EfT7Ae', '.vmXUDf']
            stops_text = "1 parada"  # Default assumption
            
            for selector in stops_selectors:
                try:
                    stops_elem = element.find_element(By.CSS_SELECTOR, selector)
                    stops_text = stops_elem.text.strip()
                    if stops_text:
                        break
                except NoSuchElementException:
                    continue
            
            stops = self._parse_stops(stops_text)
            
            # Try to extract duration
            duration_selectors = ['[data-test-id="duration"]', '.gvkrdb', '.Ak5kof']
            duration = "N/A"
            
            for selector in duration_selectors:
                try:
                    duration_elem = element.find_element(By.CSS_SELECTOR, selector)
                    duration = duration_elem.text.strip()
                    if duration:
                        break
                except NoSuchElementException:
                    continue
            
            # Get current page URL as booking reference
            booking_url = self.driver.current_url
            
            return FlightResult(
                price=price,
                currency='BRL',
                airline=airline,
                departure_time='N/A',
                arrival_time='N/A', 
                duration=duration,
                stops=stops,
                booking_url=booking_url
            )
            
        except Exception as e:
            logger.warning(f"Error parsing flight element: {str(e)}")
            return None
    
    def close(self):
        """Close WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()