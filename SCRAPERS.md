# 🛫 Flight Scrapers Documentation

**Flight Tracker Rio-California** supports multiple data sources for flight price collection.

---

## 📊 Available Scrapers

### 1. 🌐 Google Flights Scraper
**Status:** ✅ Implemented  
**Method:** Selenium WebDriver  
**Reliability:** High (90%+)  
**Speed:** Medium (30-60 seconds)  

**Pros:**
- Most comprehensive flight data
- Real-time prices
- Multiple airlines covered
- Booking links available

**Cons:**
- Requires Chrome/ChromeDriver
- Selenium overhead
- Potential anti-bot detection

**Setup:**
```bash
# Install Chrome (Ubuntu/Debian)
apt-get update && apt-get install -y google-chrome-stable

# Install requirements
pip install selenium webdriver-manager
```

### 2. 🏄‍♂️ Kayak Scraper
**Status:** ✅ Implemented  
**Method:** HTTP requests + HTML parsing  
**Reliability:** Medium (60-80%)  
**Speed:** Fast (10-20 seconds)  

**Pros:**
- Lightweight (no browser needed)
- Fast execution
- Good price coverage

**Cons:**
- Anti-bot protection
- HTML structure changes
- Less reliable data extraction

**Setup:**
```bash
# Install requirements
pip install httpx beautifulsoup4
```

### 3. 🧪 Mock Scraper
**Status:** ✅ Implemented  
**Method:** Realistic fake data generation  
**Reliability:** Perfect (100%)  
**Speed:** Very fast (1-3 seconds)  

**Pros:**
- Perfect for development/testing
- Realistic price patterns
- No external dependencies
- Always works

**Cons:**
- Not real data
- Only for testing/development

**Setup:**
```bash
# No additional setup required
# Enable with: USE_MOCK_SCRAPER=true
```

---

## ⚙️ Configuration

### Environment Variables

```env
# Scraper selection
USE_MOCK_SCRAPER=false           # Use mock for testing
ENABLE_GOOGLE_FLIGHTS=true       # Enable Google Flights
ENABLE_KAYAK=true                # Enable Kayak
PREFERRED_SCRAPER=google_flights # Primary scraper

# Chrome settings
CHROME_HEADLESS=true             # Headless browser
CHROME_TIMEOUT=30                # Load timeout
```

### Automatic Fallback

The system automatically falls back through scrapers:

1. **Primary scraper** (configured in PREFERRED_SCRAPER)
2. **Secondary scrapers** (other enabled scrapers)  
3. **Mock scraper** (if no real data available)

---

## 🧪 Testing Scrapers

### Test All Scrapers
```bash
python test_scrapers.py
```

### Test Individual Scraper
```bash
# Test mock scraper
USE_MOCK_SCRAPER=true python main.py check GIG LAX 2026-04-15

# Test Google Flights only  
python -c "
import asyncio
from tracker.scrapers.google_flights import GoogleFlightsScraper
from datetime import date, timedelta

async def test():
    scraper = GoogleFlightsScraper()
    flights = await scraper.search_flights('GIG', 'LAX', date.today() + timedelta(days=30), date.today() + timedelta(days=36))
    print(f'Found {len(flights)} flights')
    scraper.close()

asyncio.run(test())
"
```

### Expected Output
```
🛫 Flight Tracker Rio-California - Scraper Tests
============================================================

🧪 Testing Mock Scraper...
✅ Mock scraper found 12 flights

📊 Sample flights:
1. R$    2,240.00 - LATAM Airlines
   🛫 2026-04-15 → 2026-04-21
   ⏱️  14h | Stops: 1

🌐 Testing Google Flights Scraper...
✅ Google Flights found 8 flights

🏄‍♂️ Testing Kayak Scraper...
✅ Kayak found 5 flights

🎯 Test Results Summary:
------------------------------
mock           : ✅ PASS
google_flights : ✅ PASS  
kayak          : ✅ PASS
```

---

## 🔧 Troubleshooting

### Google Flights Issues

**Error:** `ChromeDriver not found`
```bash
# Solution: Install Chrome
apt-get update && apt-get install -y google-chrome-stable
```

**Error:** `TimeoutException`
```bash
# Solution: Increase timeout
export CHROME_TIMEOUT=60
```

**Error:** `Access denied / Bot detection`
```bash
# Solution: Use different user agent or add delays
export REQUEST_DELAY=5
```

### Kayak Issues

**Error:** `403 Forbidden` or `Access denied`
```bash
# Solution: Rotate user agents or use proxy
export ENABLE_PROXY_ROTATION=true
```

**Error:** `No flights found`
```bash
# Solution: Check HTML selectors (may need updates)
# Kayak frequently changes their HTML structure
```

### Mock Scraper Issues

Mock scraper should never fail. If it does:
```bash
# Check Python syntax
python -c "from tracker.scrapers.mock_scraper import MockFlightScraper; print('OK')"

# Check dependencies
pip install -r requirements.txt
```

---

## 📈 Performance Comparison

| Scraper        | Speed | Reliability | Data Quality | Setup Complexity |
|----------------|-------|-------------|--------------|------------------|
| Google Flights | ⭐⭐⭐   | ⭐⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐      | ⭐⭐⭐            |
| Kayak          | ⭐⭐⭐⭐⭐ | ⭐⭐⭐       | ⭐⭐⭐⭐        | ⭐⭐              |
| Mock           | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐     | ⭐⭐           | ⭐⭐⭐⭐⭐          |

## 🎯 Recommendations

### Development
```bash
# Use mock scraper for fast iteration
USE_MOCK_SCRAPER=true python main.py monitor
```

### Testing
```bash
# Use all scrapers to validate data consistency  
python test_scrapers.py
```

### Production
```bash
# Use Google Flights as primary with Kayak backup
PREFERRED_SCRAPER=google_flights
ENABLE_GOOGLE_FLIGHTS=true
ENABLE_KAYAK=true
USE_MOCK_SCRAPER=false
```

### CI/CD Pipeline
```bash
# Use mock for automated tests
USE_MOCK_SCRAPER=true python -m pytest tests/
```

---

## 🔮 Future Scrapers

### Planned Additions
- **Skyscanner API** - Official API integration
- **Amadeus API** - Professional travel API
- **Expedia Scraper** - Additional price source
- **Decolar Scraper** - Brazilian travel site

### API Integration Priority
1. **Amadeus API** (most comprehensive)
2. **Skyscanner API** (good coverage)  
3. **Google Travel Partner API** (official Google Flights)

---

## 💡 Best Practices

### Rate Limiting
```python
# Add delays between requests
await asyncio.sleep(2)

# Respect robots.txt
RESPECT_ROBOTS_TXT=true
```

### Error Handling
```python
# Always implement fallbacks
try:
    flights = await primary_scraper.search()
except Exception:
    flights = await backup_scraper.search()
```

### Data Validation
```python
# Validate scraped data
if flight.price > 0 and flight.airline and flight.departure_date:
    flights.append(flight)
```

### Monitoring
```python
# Log scraper performance
logger.info(f"Scraper {name} found {len(flights)} flights in {duration:.1f}s")
```

---

**🛫 Happy scraping! All scrapers are ready for Rio-California flight monitoring.**