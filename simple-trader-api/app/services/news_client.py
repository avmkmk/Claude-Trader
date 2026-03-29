"""
News Client Service

Provides market news from external APIs (Marketaux and Alpha Vantage).
Combines results from both sources and handles API errors gracefully.
"""

import requests
from typing import List, Dict, Optional
from app.config import settings


class NewsClient:
    """
    Client for fetching market news from external APIs.
    
    Supports Marketaux and Alpha Vantage APIs with filtering
    by symbols and keywords.
    """
    
    def __init__(self):
        """Initialize the news client with API keys from settings."""
        self.marketaux_key = settings.MARKETAUX_API_KEY
        self.alphavantage_key = settings.ALPHA_VANTAGE_API_KEY
    
    
    def get_marketaux_news(self, symbols: Optional[List[str]] = None, 
                           keywords: Optional[str] = None,
                           limit: int = 20) -> List[Dict]:
        """
        Fetch news from Marketaux API.
        
        Args:
            symbols: Optional list of stock symbols to filter
            keywords: Optional keywords for search
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of news articles or error message
        """
        if not self.marketaux_key:
            return self._dummy_news("marketaux")
        
        url = "https://api.marketaux.com/v1/news"
        params = {
            "filter_entities": "true",
            "api_key": self.marketaux_key,
            "limit": limit
        }
        
        if symbols:
            params["symbols"] = ",".join(symbols)
        if keywords:
            params["keywords"] = keywords
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._parse_marketaux_news(data)
            else:
                return [{"error": f"API error: {response.status_code}"}]
        except Exception as e:
            return [{"error": str(e)}]
    
    
    def _parse_marketaux_news(self, data: dict) -> List[Dict]:
        """
        Parse Marketaux API response into standardized format.
        
        Args:
            data: Raw API response JSON
            
        Returns:
            List of parsed news articles
        """
        news = []
        for item in data.get("data", []):
            news.append({
                "title": item.get("title", ""),
                "summary": item.get("description", "")[:200],
                "source": "Marketaux",
                "url": item.get("url", ""),
                "published_at": item.get("published_at", ""),
                "symbols": [e.get("symbol") for e in item.get("entities", [])],
                "sentiment": "Neutral"
            })
        return news
    
    
    def get_alphavantage_news(self, tickers: Optional[str] = None,
                              keywords: Optional[str] = None) -> List[Dict]:
        """
        Fetch news from Alpha Vantage API.
        
        Args:
            tickers: Optional comma-separated stock tickers
            keywords: Optional keywords for search
            
        Returns:
            List of news articles or error message
        """
        if not self.alphavantage_key:
            return self._dummy_news("alphavantage")
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.alphavantage_key,
            "limit": 20
        }
        
        if tickers:
            params["tickers"] = tickers
        if keywords:
            params["keywords"] = keywords
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "feed" in data:
                    return self._parse_alphavantage_news(data)
                elif "Note" in data or "Information" in data:
                    return [{"error": "API limit reached"}]
                else:
                    return [{"error": "No data"}]
            else:
                return [{"error": f"API error: {response.status_code}"}]
        except Exception as e:
            return [{"error": str(e)}]
    
    
    def _parse_alphavantage_news(self, data: dict) -> List[Dict]:
        """
        Parse Alpha Vantage API response into standardized format.
        
        Args:
            data: Raw API response JSON
            
        Returns:
            List of parsed news articles with sentiment
        """
        news = []
        for item in data.get("feed", []):
            news.append({
                "title": item.get("title", ""),
                "summary": item.get("summary", "")[:200],
                "source": item.get("source", "Alpha Vantage"),
                "url": item.get("url", ""),
                "published_at": item.get("time_published", ""),
                "sentiment": item.get("overall_sentiment_label", "Neutral"),
                "tickers": [t.get("ticker") for t in item.get("ticker_sentiment", [])]
            })
        return news
    
    
    def get_news_combined(self, symbols: Optional[List[str]] = None,
                          keywords: Optional[str] = None) -> List[Dict]:
        """
        Fetch and combine news from both Marketaux and Alpha Vantage.
        
        Results are sorted by publish date (newest first) and limited to 40 articles.
        
        Args:
            symbols: Optional list of stock symbols to filter
            keywords: Optional keywords for search
            
        Returns:
            Combined and sorted list of news articles
        """
        all_news = []
        
        # Fetch from both sources
        marketaux_news = self.get_marketaux_news(symbols, keywords)
        all_news.extend(marketaux_news)
        
        alphavantage_news = self.get_alphavantage_news(
            ",".join(symbols) if symbols else None,
            keywords
        )
        all_news.extend(alphavantage_news)
        
        # Sort by publish date (newest first)
        all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        # Limit to 40 articles
        return all_news[:40]
    
    
    def _dummy_news(self, source: str) -> List[Dict]:
        """
        Get placeholder news when API key is not configured.
        
        Args:
            source: Name of the news source (marketaux or alphavantage)
            
        Returns:
            List with single placeholder article
        """
        return [
            {
                "title": f"Configure {source.upper()} API key to get live news",
                "summary": f"Set {source.upper()}_API_KEY in .env file. Get free key at marketaux.com or alphavantage.co",
                "source": "System",
                "url": "",
                "published_at": "",
                "symbols": [],
                "sentiment": "Neutral"
            }
        ]


# Global news client instance
news_client = NewsClient()
