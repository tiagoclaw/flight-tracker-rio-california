"""
Price trend analysis for flight data.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from statistics import mean, median, stdev

class PriceAnalyzer:
    """Analyzes flight price trends and patterns."""
    
    def __init__(self, db_ops):
        self.db_ops = db_ops
    
    def get_average_price(self, route: str, days: int = 30) -> Optional[float]:
        """Get average price for a route over specified days."""
        flights = self.db_ops.get_recent_flights(route, days)
        
        if not flights:
            return None
        
        prices = [f.price for f in flights]
        return mean(prices)
    
    def analyze_trends(self, route: str, days: int = 60) -> Dict:
        """Analyze price trends for a route."""
        flights = self.db_ops.get_recent_flights(route, days)
        
        if len(flights) < 10:
            return {"error": "Insufficient data for trend analysis"}
        
        # Split into recent and older periods
        mid_point = len(flights) // 2
        recent_flights = flights[:mid_point]
        older_flights = flights[mid_point:]
        
        recent_avg = mean([f.price for f in recent_flights])
        older_avg = mean([f.price for f in older_flights])
        
        change_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        # Determine trend direction
        if change_percent > 5:
            direction = "increasing"
        elif change_percent < -5:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Calculate volatility
        all_prices = [f.price for f in flights]
        volatility = "high" if stdev(all_prices) > mean(all_prices) * 0.2 else "low"
        
        # Generate recommendation
        if direction == "decreasing":
            recommendation = "Wait - prices trending down"
        elif direction == "increasing":
            recommendation = "Book soon - prices trending up"
        else:
            recommendation = "Monitor - stable pricing"
        
        return {
            "direction": direction,
            "change_percent": round(change_percent, 1),
            "volatility": volatility,
            "recommendation": recommendation,
            "recent_avg": round(recent_avg, 2),
            "older_avg": round(older_avg, 2),
        }