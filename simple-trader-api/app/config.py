"""
Configuration Settings

Loads environment variables and provides centralized access to application settings.
Supports configuration via .env file in the simple-trader-api directory.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Determine the base directory (parent of the app/ folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    """
    Application configuration settings.
    
    All settings can be overridden via environment variables or .env file.
    """
    
    # Nubra Broker Configuration
    # Required for authentication and trading via Nubra broker
    NUBRA_MPIN = os.environ.get("NUBRA_MPIN") or os.environ.get("MPIN")
    """Nubra account MPIN for authentication"""
    
    NUBRA_CLIENT_ID = os.environ.get("NUBRA_CLIENT_ID", "")
    """Nubra client ID for API access"""
    
    PHONE_NO = os.environ.get("PHONE_NO", "")
    """Phone number associated with Nubra account (optional)"""
    
    
    # Database and Data Paths
    DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "data" / "dashboard.db"))
    """Path to SQLite database for watchlist, signals, and settings"""
    
    DAILY_DATA_PATH = os.environ.get("DAILY_DATA_PATH", str(BASE_DIR.parent / "historical_Indian_equity_data" / "daily" / "eod2"))
    """Path to historical daily OHLCV data for backtesting"""
    
    
    # Cache and Session Settings
    CACHE_TTL = 30
    """Time-to-live for cached data in seconds"""
    
    SESSION_EXPIRE_SECONDS = 86400
    """Session expiration time in seconds (default: 24 hours)"""
    
    
    # API Keys for External Services
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    """Google Gemini API key for AI chat and analysis features"""
    
    MARKETAUX_API_KEY = os.environ.get("MARKETAUX_API_KEY", "")
    """Marketaux API key for market news"""
    
    ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    """Alpha Vantage API key for market news and sentiment data"""


# Global settings instance for easy import throughout the application
settings = Settings()
