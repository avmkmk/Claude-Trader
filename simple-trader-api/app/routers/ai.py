"""
AI Chat and Analysis Endpoints

Provides AI-powered chat and analysis using Google Gemini.
Includes stock analysis, portfolio analysis, and trading insights.
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.auth import session_manager
from app.services.ai_client import ai_client


# Create router with /ai prefix
router = APIRouter(prefix="/ai", tags=["ai"])


# Request Models

class ChatRequest(BaseModel):
    """Request model for general chat"""
    message: str
    """User's chat message"""
    context: Optional[Dict] = None
    """Optional context (holdings, watchlist, trades)"""


class AnalyzeStockRequest(BaseModel):
    """Request model for stock analysis"""
    symbol: str
    """Stock symbol to analyze"""
    context: Optional[Dict] = None
    """Optional additional context"""


class SuggestStocksRequest(BaseModel):
    """Request model for stock suggestions"""
    criteria: str = "momentum"
    """Trading strategy criteria (momentum, mean_reversion, breakout)"""
    watchlist: Optional[List[str]] = None
    """Optional user's watchlist for context"""


class AnalyzeHoldingsRequest(BaseModel):
    """Request model for portfolio analysis"""
    holdings: List[Dict]
    """List of holdings with symbol, quantity, prices, P&L"""


class AnalyzeTradesRequest(BaseModel):
    """Request model for trade history analysis"""
    trades: List[Dict]
    """List of completed trades with P&L"""


# API Endpoints

@router.post("/chat")
async def chat(
    request: ChatRequest,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    General chat with AI assistant.
    
    Ask questions about trading, get market insights, or request explanations.
    
    Args:
        request: ChatRequest with message and optional context
        x_session_id: Session ID from header for authentication
        
    Returns:
        AI response message
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    response = ai_client.chat(request.message, request.context)
    return {"response": response}


@router.post("/analyze-stock")
async def analyze_stock(
    request: AnalyzeStockRequest,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Analyze a specific stock for trading opportunities.
    
    Provides technical outlook, support/resistance levels, and strategy suggestions.
    
    Args:
        request: AnalyzeStockRequest with stock symbol
        x_session_id: Session ID from header for authentication
        
    Returns:
        Stock analysis from AI
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    response = ai_client.analyze_stock(request.symbol, request.context)
    return {"response": response}


@router.post("/suggest-stocks")
async def suggest_stocks(
    request: SuggestStocksRequest,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Get AI-suggested stocks for a trading strategy.
    
    Returns 5 stock suggestions with company names and rationale.
    
    Args:
        request: SuggestStocksRequest with criteria and optional watchlist
        x_session_id: Session ID from header for authentication
        
    Returns:
        Stock suggestions from AI
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    response = ai_client.suggest_stocks(request.criteria, request.watchlist)
    return {"response": response}


@router.post("/analyze-holdings")
async def analyze_holdings(
    request: AnalyzeHoldingsRequest,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Analyze user's portfolio holdings.
    
    Provides portfolio health assessment, position recommendations, and diversification tips.
    
    Args:
        request: AnalyzeHoldingsRequest with list of holdings
        x_session_id: Session ID from header for authentication
        
    Returns:
        Portfolio analysis from AI
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    response = ai_client.analyze_holdings(request.holdings)
    return {"response": response}


@router.post("/analyze-trades")
async def analyze_trades(
    request: AnalyzeTradesRequest,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Analyze user's trade history.
    
    Provides performance assessment, pattern analysis, and strategy recommendations.
    
    Args:
        request: AnalyzeTradesRequest with list of trades
        x_session_id: Session ID from header for authentication
        
    Returns:
        Trade analysis from AI
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    response = ai_client.analyze_trade_history(request.trades)
    return {"response": response}
