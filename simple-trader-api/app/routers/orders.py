"""
Order History Endpoints

Provides access to user's historical order and trade data.
Currently returns mock data - can be extended to integrate with broker APIs.
"""

from fastapi import APIRouter, Header
from typing import List
from app.auth import session_manager


# Create router with orders tag
router = APIRouter(tags=["orders"])


# Mock order history for demonstration
# In production, this would fetch from Nubra/Upstox broker APIs
MOCK_ORDERS = [
    {
        "symbol": "HDFCBANK",
        "quantity": 50,
        "entry_price": 1650.00,
        "exit_price": 1700.00,
        "entry_date": "2025-03-01",
        "exit_date": "2025-03-15",
        "pnl": 2500.00,
        "exchange": "NSE",
        "order_type": "MARKET",
        "transaction_type": "BUY",
        "timestamp": "2025-03-15T10:30:00",
    },
    {
        "symbol": "INFY",
        "quantity": 100,
        "entry_price": 1450.00,
        "exit_price": 1420.00,
        "entry_date": "2025-03-05",
        "exit_date": "2025-03-10",
        "pnl": -3000.00,
        "exchange": "NSE",
        "order_type": "LIMIT",
        "transaction_type": "BUY",
        "timestamp": "2025-03-10T14:15:00",
    },
    {
        "symbol": "WIPRO",
        "quantity": 200,
        "entry_price": 520.00,
        "exit_price": 545.00,
        "entry_date": "2025-02-20",
        "exit_date": "2025-03-01",
        "pnl": 5000.00,
        "exchange": "NSE",
        "order_type": "MARKET",
        "transaction_type": "BUY",
        "timestamp": "2025-03-01T09:45:00",
    },
]


@router.get("/orders")
async def get_orders(x_session_id: str = Header(alias="X-Session-ID")):
    """
    Get user's historical order/trade history.
    
    Returns a list of completed trades with entry/exit prices and P&L.
    
    Args:
        x_session_id: Session ID from header for authentication
        
    Returns:
        List of completed orders with trade details and profit/loss
    """
    # Validate session before returning data
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}
    
    return MOCK_ORDERS
