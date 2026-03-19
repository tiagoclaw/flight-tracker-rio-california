"""
Database models for flight price tracking.
"""

from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class CabinClass(str, Enum):
    """Flight cabin class options."""
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy" 
    BUSINESS = "business"
    FIRST = "first"

class AlertType(str, Enum):
    """Types of price alerts."""
    PRICE_DROP = "price_drop"      # Price dropped by X%
    DEAL_ALERT = "deal_alert"      # Price significantly below average
    TARGET_PRICE = "target_price"  # Price reached specific target
    TREND_ALERT = "trend_alert"    # Price trend change detected

class Flight(Base):
    """Flight price record."""
    
    __tablename__ = "flights"
    
    id = Column(Integer, primary_key=True)
    
    # Route information
    departure_airport = Column(String(3), nullable=False)  # GIG, SDU
    arrival_airport = Column(String(3), nullable=False)    # LAX, SFO
    
    # Trip dates
    departure_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=False)
    duration_days = Column(Integer, nullable=False, default=6)
    
    # Pricing
    price = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")
    taxes_included = Column(Boolean, default=True)
    
    # Flight details
    airline = Column(String(50))
    flight_number = Column(String(20))
    cabin_class = Column(String(20), default=CabinClass.ECONOMY)
    stops = Column(Integer, default=0)  # 0 = direct, 1+ = stops
    total_duration_minutes = Column(Integer)  # Total travel time
    
    # Booking details
    booking_url = Column(Text)
    booking_site = Column(String(50))
    seats_available = Column(Integer)
    
    # Metadata
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(50), nullable=False)  # google_flights, kayak, etc.
    
    # Data quality
    is_cached = Column(Boolean, default=False)
    confidence_score = Column(Float, default=1.0)  # 0-1 data reliability
    
    @property
    def route_code(self) -> str:
        """Get route code like GIG-LAX."""
        return f"{self.departure_airport}-{self.arrival_airport}"
    
    @property
    def price_per_day(self) -> float:
        """Calculate price per day of trip."""
        return self.price / self.duration_days if self.duration_days > 0 else self.price
    
    def __repr__(self) -> str:
        return (f"<Flight {self.route_code} {self.departure_date} "
                f"R$ {self.price:.2f} via {self.source}>")

class PriceAlert(Base):
    """User price alert configuration."""
    
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True)
    
    # Alert target
    route = Column(String(10), nullable=False)  # GIG-LAX, GIG-SFO, etc.
    user_email = Column(String(100), nullable=False)
    user_telegram_id = Column(String(20))
    
    # Alert conditions
    alert_type = Column(String(20), nullable=False)  # AlertType enum
    threshold_value = Column(Float, nullable=False)  # Percentage or absolute value
    target_price = Column(Float)  # For TARGET_PRICE alerts
    
    # Date preferences
    preferred_departure_start = Column(Date)
    preferred_departure_end = Column(Date)
    flexible_dates = Column(Boolean, default=True)
    
    # Flight preferences
    max_stops = Column(Integer, default=2)
    preferred_cabin_class = Column(String(20), default=CabinClass.ECONOMY)
    min_duration_days = Column(Integer, default=5)
    max_duration_days = Column(Integer, default=7)
    
    # Alert settings
    active = Column(Boolean, default=True)
    max_alerts_per_day = Column(Integer, default=3)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return (f"<PriceAlert {self.route} {self.alert_type} "
                f"threshold={self.threshold_value} user={self.user_email}>")

class PriceHistory(Base):
    """Aggregated price statistics for routes."""
    
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    
    # Route & date
    route = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    
    # Price statistics for the day
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    median_price = Column(Float)
    
    # Data points
    sample_count = Column(Integer, nullable=False)
    source_count = Column(Integer, default=1)  # How many sources
    
    # Market conditions
    demand_level = Column(String(20))  # low, medium, high, peak
    seasonality_factor = Column(Float, default=1.0)
    
    # Metadata  
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return (f"<PriceHistory {self.route} {self.date} "
                f"avg=R$ {self.avg_price:.2f} samples={self.sample_count}>")

class ScrapingLog(Base):
    """Log of scraping attempts and results."""
    
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Scraping session
    source = Column(String(50), nullable=False)
    route = Column(String(10), nullable=False)
    departure_date = Column(Date, nullable=False)
    
    # Results
    prices_found = Column(Integer, default=0)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # Performance
    duration_seconds = Column(Float)
    requests_made = Column(Integer, default=1)
    
    # Metadata
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    
    def __repr__(self) -> str:
        return (f"<ScrapingLog {self.source} {self.route} "
                f"{self.departure_date} success={self.success}>")

# Database configuration
@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    
    database_url: str = "sqlite:///data/flight_prices.db"
    echo_sql: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    
class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.engine = create_engine(
            self.config.database_url,
            echo=self.config.echo_sql,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get database session."""
        return self.SessionLocal()
        
    def drop_tables(self):
        """Drop all database tables (development only)."""
        Base.metadata.drop_all(bind=self.engine)