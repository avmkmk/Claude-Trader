"""
Portfolio Holdings Endpoints

Provides access to user's current portfolio holdings.
Currently returns mock data - can be extended to integrate with broker APIs.
"""

from fastapi import APIRouter, Header
from typing import List
from app.auth import session_manager


# Create router with holdings tag
router = APIRouter(tags=["holdings"])


# Mock holdings data for demonstration
# In production, this would fetch from Nubra/Upstox broker APIs
MOCK_HOLDINGS = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "avg_price": 2500.00,
        "current_price": 2650.00,
        "pnl": 15000.00,
        "pnl_percent": 6.0,
        "exchange": "NSE",
        "product": "CNC",
    },
    {
        "symbol": "HDFCBANK",
        "quantity": 50,
        "avg_price": 1650.00,
        "current_price": 1700.00,
        "pnl": 2500.00,
        "pnl_percent": 3.03,
        "exchange": "NSE",
        "product": "CNC",
    },
    {
        "symbol": "INFY",
        "quantity": 75,
        "avg_price": 1450.00,
        "current_price": 1420.00,
        "pnl": -2250.00,
        "pnl_percent": -2.07,
        "exchange": "NSE",
        "product": "CNC",
    },
    {
        "symbol": "TCS",
        "quantity": 25,
        "avg_price": 3800.00,
        "current_price": 3950.00,
        "pnl": 3750.00,
        "pnl_percent": 3.95,
        "exchange": "NSE",
        "product": "CNC",
    },
]


@router.get("/holdings")
async def get_holdings(x_session_id: str = Header(alias="X-Session-ID")):
    """
    Get user's current portfolio holdings.
    
    Returns a list of all current positions with quantity, average price,
    current market price, and profit/loss information.
    
    Args:
        x_session_id: Session ID from header for authentication
        
    Returns:
        List of holdings with symbol, quantity, prices, and P&L
    """
    # Validate session before returning data
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    return MOCK_HOLDINGS
