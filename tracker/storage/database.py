"""
Database operations for flight price tracking.
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from .models import Flight, PriceAlert, PriceHistory, DatabaseManager

class DatabaseOperations:
    """Database operations wrapper."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_flights(self, flights: List[Flight]) -> int:
        """Save flights to database."""
        session = self.db_manager.get_session()
        try:
            session.add_all(flights)
            session.commit()
            return len(flights)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_recent_flights(self, route: str, days: int = 30) -> List[Flight]:
        """Get recent flights for a route."""
        departure, arrival = route.split('-')
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        session = self.db_manager.get_session()
        try:
            flights = session.query(Flight).filter(
                Flight.departure_airport == departure,
                Flight.arrival_airport == arrival,
                Flight.checked_at >= cutoff_date
            ).order_by(Flight.checked_at.desc()).all()
            return flights
        finally:
            session.close()
    
    def get_active_alerts(self) -> List[PriceAlert]:
        """Get all active price alerts."""
        session = self.db_manager.get_session()
        try:
            alerts = session.query(PriceAlert).filter(
                PriceAlert.active == True
            ).all()
            return alerts
        finally:
            session.close()
    
    def save_alert(self, alert: PriceAlert) -> int:
        """Save price alert to database."""
        session = self.db_manager.get_session()
        try:
            session.add(alert)
            session.commit()
            return alert.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_alert_triggered(self, alert_id: int):
        """Update alert as triggered."""
        session = self.db_manager.get_session()
        try:
            alert = session.query(PriceAlert).get(alert_id)
            if alert:
                alert.last_triggered = datetime.utcnow()
                alert.trigger_count += 1
                session.commit()
        finally:
            session.close()