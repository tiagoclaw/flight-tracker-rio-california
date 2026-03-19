"""
Flight Tracker Rio-California

Automated flight price monitoring system for Rio de Janeiro to Los Angeles/San Francisco routes.
"""

__version__ = "1.0.0"
__author__ = "Tiago Mendes Dantas"
__email__ = "tiago@brazilfinance.com.br"

from .tracker import FlightTracker
from .storage.models import Flight, PriceAlert
from .analyzer.trends import PriceAnalyzer
from .notifiers.email import EmailNotifier
from .notifiers.telegram import TelegramNotifier

__all__ = [
    "FlightTracker",
    "Flight", 
    "PriceAlert",
    "PriceAnalyzer",
    "EmailNotifier",
    "TelegramNotifier",
]