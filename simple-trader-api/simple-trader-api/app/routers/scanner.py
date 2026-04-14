"""
Scanner Endpoints

Provides Chartink scraping and ATH analysis functionality.
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel
from app.auth import session_manager
from app.services.chartink_scraper import ChartinkScraper
import sqlite3
import os
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router with scanner tag
router = APIRouter(tags=["scanner"])

# Database path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "dashboard.db")


def get_db():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class ScrapeResponse(BaseModel):
    """Response model for scrape operation"""
    success: bool
    total_found: int
    new_candidates: int
    duplicates_skipped: int
    errors: List[str] = []


@router.post("/scanner/scrape-chartink")
async def scrape_chartink(x_session_id: str = Header(alias="X-Session-ID")) -> ScrapeResponse:
    """
    Trigger Chartink scraping for both screener URLs.

    Scrapes stocks from:
    - Within 2% of 52-week highs screener
    - Stage 2 trend template screener

    Stores results in candidates table for user review.

    Args:
        x_session_id: Session ID from header for authentication

    Returns:
        ScrapeResponse with counts and any errors
    """
    if not session_manager.validate_session(x_session_id):
        return ScrapeResponse(
            success=False,
            total_found=0,
            new_candidates=0,
            duplicates_skipped=0,
            errors=["Not authenticated"]
        )

    try:
        logger.info("Starting Chartink scraping...")

        # Run scraper
        scraper = ChartinkScraper()
        result = scraper.scrape_both_screeners()

        stocks = result.get("stocks", [])
        errors = result.get("errors", [])

        logger.info(f"Scraping completed: {len(stocks)} stocks found")

        # Store in database
        conn = get_db()
        cursor = conn.cursor()

        new_candidates = 0
        duplicates_skipped = 0

        for stock in stocks:
            try:
                cursor.execute("""
                    INSERT INTO candidates (symbol, source)
                    VALUES (?, ?)
                """, (stock["symbol"], stock["source"]))
                new_candidates += 1
            except sqlite3.IntegrityError:
                # Duplicate entry (symbol + source already exists)
                duplicates_skipped += 1

        conn.commit()
        conn.close()

        logger.info(f"Stored in database: {new_candidates} new, {duplicates_skipped} duplicates")

        return ScrapeResponse(
            success=True,
            total_found=len(stocks),
            new_candidates=new_candidates,
            duplicates_skipped=duplicates_skipped,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error in scrape_chartink: {e}")
        return ScrapeResponse(
            success=False,
            total_found=0,
            new_candidates=0,
            duplicates_skipped=0,
            errors=[str(e)]
        )


class Candidate(BaseModel):
    """Model for candidate stock"""
    id: int
    symbol: str
    source: str
    current_price: float | None
    week_52_high: float | None
    distance_from_high: float | None
    scraped_at: str


@router.get("/scanner/candidates")
async def get_candidates(x_session_id: str = Header(alias="X-Session-ID")) -> List[Candidate]:
    """
    Get all candidate stocks from recent scrapes.

    Args:
        x_session_id: Session ID from header for authentication

    Returns:
        List of candidate stocks ordered by scraped date (newest first)
    """
    if not session_manager.validate_session(x_session_id):
        return []

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, symbol, source, current_price, week_52_high,
                   distance_from_high, scraped_at
            FROM candidates
            ORDER BY scraped_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            Candidate(
                id=row["id"],
                symbol=row["symbol"],
                source=row["source"],
                current_price=row["current_price"],
                week_52_high=row["week_52_high"],
                distance_from_high=row["distance_from_high"],
                scraped_at=row["scraped_at"]
            )
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error getting candidates: {e}")
        return []


class AddToWatchlistResponse(BaseModel):
    """Response model for add to watchlist operation"""
    success: bool
    error: str | None = None
    analysis: Dict | None = None


@router.post("/scanner/candidates/{symbol}/add-to-watchlist")
async def add_candidate_to_watchlist(
    symbol: str,
    x_session_id: str = Header(alias="X-Session-ID")
) -> AddToWatchlistResponse:
    """
    Move a candidate to watchlist and run ATH analysis.

    This endpoint:
    1. Inserts stock into watchlist
    2. Deletes from candidates
    3. Runs immediate ATH analysis
    4. Updates watchlist with phase data

    Args:
        symbol: Stock symbol to add
        x_session_id: Session ID from header for authentication

    Returns:
        AddToWatchlistResponse with analysis result
    """
    if not session_manager.validate_session(x_session_id):
        return AddToWatchlistResponse(
            success=False,
            error="Not authenticated"
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check if already in watchlist
        cursor.execute("SELECT 1 FROM watchlist WHERE symbol = ?", (symbol,))
        if cursor.fetchone():
            conn.close()
            return AddToWatchlistResponse(
                success=False,
                error=f"{symbol} already in watchlist"
            )

        # Insert into watchlist
        cursor.execute("""
            INSERT INTO watchlist (symbol, name, type)
            VALUES (?, ?, ?)
        """, (symbol, "", "EQUITY"))

        # Delete from candidates
        cursor.execute("DELETE FROM candidates WHERE symbol = ?", (symbol,))

        conn.commit()
        conn.close()

        # TODO: Run ATH analysis immediately
        # This will be implemented in Phase 3 when ATHAnalyzer is built
        # For now, just return success without analysis

        logger.info(f"Added {symbol} to watchlist")

        return AddToWatchlistResponse(
            success=True,
            analysis=None  # Will be populated in Phase 3
        )

    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        return AddToWatchlistResponse(
            success=False,
            error=str(e)
        )
