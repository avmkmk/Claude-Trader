"""
Market News Endpoints

Provides market news from external APIs (Marketaux and Alpha Vantage).
Supports filtering by symbols and keywords.
"""

from fastapi import APIRouter, Header, Query
from typing import Optional, List
from app.auth import session_manager
from app.services.news_client import news_client


# Create router with news tag
router = APIRouter(tags=["news"])


@router.get("/news")
async def get_news(
    x_session_id: str = Header(alias="X-Session-ID"),
    symbols: Optional[str] = Query(None, description="Comma-separated symbols to filter news"),
    keywords: Optional[str] = Query(None, description="Search keywords for news filtering")
):
    """
    Get market news from external APIs.
    
    Combines news from Marketaux and Alpha Vantage APIs.
    Results can be filtered by stock symbols or keywords.
    
    Args:
        x_session_id: Session ID from header for authentication
        symbols: Optional comma-separated list of stock symbols to filter
        keywords: Optional keywords to search for in news
        
    Returns:
        List of news articles with title, summary, source, and metadata
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    # Parse symbols string into list
    symbol_list = symbols.split(",") if symbols else None
    
    # Get combined news from both APIs
    news = news_client.get_news_combined(symbol_list, keywords)
    return news
