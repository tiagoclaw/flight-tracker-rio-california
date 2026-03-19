# 🛫 Flight Tracker: Rio → California

**Automated flight price monitoring system for Rio de Janeiro to Los Angeles/San Francisco routes.**

## Overview

- **Routes:** RIO (GIG/SDU) → LAX/SFO  
- **Trip Duration:** 6 days
- **Monitoring:** Automated price tracking + alerts
- **Storage:** Historical price data for analysis
- **Notifications:** Price drops, deals, trends

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test scrapers (recommended first step)
python test_scrapers.py

# Single price check
python main.py check GIG LAX 2026-04-15

# Start continuous monitoring
python main.py monitor

# View price history  
python main.py history GIG-LAX --days 30

# Add price alert
python main.py alert GIG-LAX your@email.com price_drop 0.15
```

## Routes Monitored

### 🇧🇷 Rio de Janeiro Departures
- **GIG** - Galeão International Airport
- **SDU** - Santos Dumont Airport

### 🇺🇸 California Destinations  
- **LAX** - Los Angeles International
- **SFO** - San Francisco International

### Trip Configuration
- **Duration:** 6 days (fixed)
- **Departure:** Flexible dates (next 90 days)
- **Class:** Economy (configurable)
- **Passengers:** 1 adult (configurable)

## Features

### 🔍 Price Monitoring
- **Real-time tracking** via multiple APIs/sources
- **Historical data** storage and analysis
- **Price alerts** via email/Telegram
- **Deal detection** (significant price drops)

### 📊 Analytics
- **Price trends** over time
- **Best booking windows** analysis
- **Seasonal patterns** identification  
- **Airline comparison** (prices, routes, timing)

### 🚨 Alerting
- **Price drop alerts** (customizable thresholds)
- **Deal notifications** (below average prices)
- **Booking reminders** (optimal timing)
- **Multiple channels** (email, Telegram, Discord)

## Architecture

```
flight-tracker-rio-california/
├── tracker/
│   ├── __init__.py
│   ├── scrapers/            # Flight data collection
│   │   ├── google_flights.py
│   │   ├── kayak.py
│   │   └── skyscanner.py
│   ├── storage/             # Data persistence
│   │   ├── database.py
│   │   └── models.py
│   ├── analyzer/            # Price analysis
│   │   ├── trends.py
│   │   └── deals.py
│   └── notifiers/           # Alert system
│       ├── email.py
│       ├── telegram.py
│       └── discord.py
├── data/                    # SQLite database + logs
├── config/                  # Configuration files
├── scripts/                 # Automation scripts
├── api/                     # Optional REST API
└── dashboard/               # Optional web dashboard
```

## Configuration

### Environment Variables
```env
# API Keys
AMADEUS_API_KEY=your_amadeus_key
SKYSCANNER_API_KEY=your_skyscanner_key

# Notification Settings  
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email
EMAIL_PASSWORD=your_app_password
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Monitoring Settings
PRICE_CHECK_INTERVAL=3600    # seconds (1 hour)
PRICE_DROP_THRESHOLD=0.15    # 15% price drop triggers alert
DEAL_THRESHOLD=0.80          # Prices 20% below average = deal
```

### Routes Configuration
```yaml
# config/routes.yaml
routes:
  - departure: GIG
    arrival: LAX
    duration_days: 6
    enabled: true
  - departure: GIG  
    arrival: SFO
    duration_days: 6
    enabled: true
  - departure: SDU
    arrival: LAX
    duration_days: 6
    enabled: false
  - departure: SDU
    arrival: SFO 
    duration_days: 6
    enabled: false
```

## Usage Examples

### Basic Price Check
```python
from tracker import FlightTracker

tracker = FlightTracker()
prices = tracker.get_prices('GIG', 'LAX', departure_date='2026-04-15', duration=6)
print(f"Current prices: {prices}")
```

### Historical Analysis
```python
from tracker.analyzer import PriceAnalyzer

analyzer = PriceAnalyzer()
trends = analyzer.get_trends('GIG-LAX', days=90)
deals = analyzer.detect_deals('GIG-LAX', threshold=0.80)
```

### Set Up Alerts
```python
from tracker.notifiers import TelegramNotifier

notifier = TelegramNotifier(bot_token, chat_id)
tracker.add_notifier(notifier)
tracker.set_alert_threshold(price_drop=0.15)  # 15% drop
```

## Deployment

### Local Development
```bash
git clone https://github.com/tiagoclaw/flight-tracker-rio-california
cd flight-tracker-rio-california
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure your API keys
python tracker.py
```

### Production (Railway)
```bash
# Deploy to Railway with automated scheduling
railway login
railway init
railway add
railway deploy
```

### GitHub Actions (Automated)
- **Scheduled runs** every hour via GitHub Actions
- **Price data** committed to repository  
- **Alerts** sent via configured channels
- **No server required** - runs on GitHub runners

## Data Storage

### SQLite Schema
```sql
CREATE TABLE flights (
    id INTEGER PRIMARY KEY,
    departure_airport VARCHAR(3),
    arrival_airport VARCHAR(3), 
    departure_date DATE,
    return_date DATE,
    price DECIMAL(10,2),
    currency VARCHAR(3),
    airline VARCHAR(50),
    booking_class VARCHAR(20),
    checked_at TIMESTAMP,
    source VARCHAR(50)
);

CREATE TABLE price_alerts (
    id INTEGER PRIMARY KEY,
    route VARCHAR(10),
    user_email VARCHAR(100),
    threshold_type VARCHAR(20), -- 'drop', 'deal', 'target'
    threshold_value DECIMAL(5,2),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);
```

### Price History Export
```bash
# Export to CSV
python scripts/export_prices.py --route GIG-LAX --format csv --days 90

# Export to JSON
python scripts/export_prices.py --route GIG-SFO --format json --all
```

## Contributing

1. **Fork repository**
2. **Create feature branch:** `git checkout -b feature/new-source`  
3. **Add flight data source** or improve existing ones
4. **Test thoroughly:** `pytest tests/`
5. **Submit pull request**

## Roadmap

### Phase 1 (Week 1) - MVP
- [x] Project setup + repository
- [x] ✅ **Google Flights scraping** (Selenium WebDriver)
- [x] ✅ **Kayak scraping** (HTTP + HTML parsing)  
- [x] ✅ **Mock scraper** (realistic test data)
- [x] ✅ **SQLite data storage** (models + operations)
- [x] ✅ **Email + Telegram alerts** (implemented)
- [x] ✅ **Price tracking system** (trends + analysis)

### Phase 2 (Week 2) - Multi-source
- [ ] Kayak integration
- [ ] Skyscanner API
- [ ] Price comparison logic
- [ ] Telegram notifications
- [ ] Automated scheduling

### Phase 3 (Week 3) - Analytics  
- [ ] Price trend analysis
- [ ] Deal detection algorithms
- [ ] Best booking window prediction
- [ ] Historical data visualization
- [ ] Web dashboard (optional)

### Phase 4 (Week 4) - Advanced
- [ ] Machine learning price predictions
- [ ] Multiple route optimization  
- [ ] Advanced notification rules
- [ ] API for external integrations
- [ ] Mobile app notifications

## License

MIT License - Feel free to use, modify, and distribute.

## Support

- **Issues:** GitHub Issues tab
- **Features:** GitHub Discussions  
- **Contact:** tiago@brazilfinance.com.br

---

**🛫 Happy travels with optimized flight prices! ✈️**