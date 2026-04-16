"""
Watchlist Management Endpoints

Provides CRUD operations for user's stock watchlist.
Stores watchlist in SQLite database with validation against historical data.
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel
from app.auth import session_manager
import sqlite3
import os


# Create router with watchlist tag
router = APIRouter(tags=["watchlist"])


# Database and data paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "dashboard.db")
DAILY_DATA_PATH = os.path.join(BASE_DIR, "..", "historical_Indian_equity_data", "daily", "eod2")


def get_db():
    """
    Get a database connection with row factory.
    
    Returns:
        sqlite3.Connection: Database connection with row factory enabled
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_valid_symbols() -> set:
    """
    Get all valid stock symbols from historical data.
    
    Returns:
        set: Set of valid stock ticker symbols
    """
    try:
        if os.path.exists(DAILY_DATA_PATH):
            return {f.replace(".csv", "").upper() for f in os.listdir(DAILY_DATA_PATH) if f.endswith(".csv")}
    except Exception:
        pass
    return set()


class WatchlistItem(BaseModel):
    """Model for watchlist item"""
    id: int
    symbol: str
    name: str | None
    type: str
    added_at: str
    notes: str | None
    phase: int | None
    status_label: str | None
    ath_value: float | None
    ath_date: str | None
    ema_200: float | None
    distance_from_ath: float | None
    last_analyzed: str | None


@router.get("/watchlist")
async def get_watchlist(x_session_id: str = Header(alias="X-Session-ID")):
    """
    Get all items in user's watchlist.
    
    Args:
        x_session_id: Session ID from header for authentication
        
    Returns:
        List of watchlist items or error message
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT id, symbol, name, type, added_at, notes,
                   phase, status_label, ath_value, ath_date,
                   ema_200, distance_from_ath, last_analyzed
            FROM watchlist
            ORDER BY added_at DESC
        """)
        rows = c.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "symbol": row[1],
                "name": row[2],
                "type": row[3],
                "added_at": row[4],
                "notes": row[5],
                "phase": row[6],
                "status_label": row[7],
                "ath_value": row[8],
                "ath_date": row[9],
                "ema_200": row[10],
                "distance_from_ath": row[11],
                "last_analyzed": row[12]
            }
            for row in rows
        ]
    except Exception as e:
        return [{"error": str(e)}]


@router.post("/watchlist")
async def add_watchlist(
    item: dict,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Add a stock to user's watchlist with source tracking.

    Validates that the symbol exists in historical data before adding.

    Args:
        item: Dictionary with symbol, optional name, source, and source_metadata
        x_session_id: Session ID from header for authentication

    Returns:
        Success status or error message
    """
    if not session_manager.validate_session(x_session_id):
        return {"success": False, "error": "Not authenticated"}

    symbol = item.get("symbol", "").strip().upper()
    if not symbol:
        return {"success": False, "error": "Symbol is required"}

    # Validate symbol exists in historical data
    valid_symbols = get_valid_symbols()
    if symbol not in valid_symbols:
        return {"success": False, "error": f"Symbol '{symbol}' not found in historical data"}

    try:
        conn = get_db()
        c = conn.cursor()

        # Check if already in watchlist
        c.execute("SELECT 1 FROM watchlist WHERE symbol = ?", (symbol,))
        if c.fetchone():
            conn.close()
            return {"success": False, "error": f"{symbol} already in watchlist"}

        # Get source tracking info (defaults to 'manual')
        source = item.get("source", "manual")
        source_metadata = item.get("source_metadata", None)

        # Insert new item with source tracking
        c.execute(
            "INSERT INTO watchlist (symbol, name, type, source, source_metadata) VALUES (?, ?, ?, ?, ?)",
            (symbol, item.get("name", ""), "EQUITY", source, source_metadata)
        )
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/watchlist/{symbol}")
async def remove_watchlist(
    symbol: str,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Remove a stock from user's watchlist.
    
    Args:
        symbol: Stock symbol to remove
        x_session_id: Session ID from header for authentication
        
    Returns:
        Success status or error message
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/watchlist/symbols")
async def get_watchlist_symbols(x_session_id: str = Header(alias="X-Session-ID")):
    """
    Get list of valid symbols for autocomplete.

    Args:
        x_session_id: Session ID from header for authentication

    Returns:
        List of valid stock symbols sorted alphabetically
    """
    if not session_manager.validate_session(x_session_id):
        return []

    try:
        valid_symbols = get_valid_symbols()
        return sorted(valid_symbols)
    except Exception:
        return []


@router.get("/watchlist/filter/{source}")
async def get_watchlist_by_source(
    source: str,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Get watchlist items filtered by source.

    Args:
        source: Filter by source ('all', 'manual', 'chartink')
        x_session_id: Session ID from header for authentication

    Returns:
        List of watchlist items filtered by source
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}

    try:
        conn = get_db()
        c = conn.cursor()

        if source == 'all':
            c.execute("""
                SELECT id, symbol, name, type, added_at, notes,
                       phase, status_label, ath_value, ath_date,
                       ema_200, distance_from_ath, last_analyzed,
                       source, source_metadata, data_as_of_date
                FROM watchlist
                ORDER BY phase DESC, added_at DESC
            """)
        else:
            # Use LIKE to match 'chartink%' for both screener types
            c.execute("""
                SELECT id, symbol, name, type, added_at, notes,
                       phase, status_label, ath_value, ath_date,
                       ema_200, distance_from_ath, last_analyzed,
                       source, source_metadata, data_as_of_date
                FROM watchlist
                WHERE source LIKE ?
                ORDER BY phase DESC, added_at DESC
            """, (f'{source}%',))

        rows = c.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "symbol": row[1],
                "name": row[2],
                "type": row[3],
                "added_at": row[4],
                "notes": row[5],
                "phase": row[6],
                "status_label": row[7],
                "ath_value": row[8],
                "ath_date": row[9],
                "ema_200": row[10],
                "distance_from_ath": row[11],
                "last_analyzed": row[12],
                "source": row[13],
                "source_metadata": row[14],
                "data_as_of_date": row[15]
            }
            for row in rows
        ]
    except Exception as e:
        return [{"error": str(e)}]
