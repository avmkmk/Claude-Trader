"""
Scanner Endpoints

Provides Chartink scraping and ATH analysis functionality.
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel
from app.auth import session_manager
from app.services.chartink_scraper import ChartinkScraper
from app.services.ath_analyzer import ATHAnalyzer
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
    unique_stocks: int
    overlap_removed: int
    new_candidates: int
    duplicates_skipped: int
    errors: List[str] = []


class DataFreshnessResponse(BaseModel):
    """Response model for data freshness check"""
    all_fresh: bool
    oldest_data_date: str | None
    oldest_days: int
    sample_size: int
    warning: str | None


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
            unique_stocks=0,
            overlap_removed=0,
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
        total_scraped = result.get("total_scraped", 0)
        unique_count = result.get("unique_count", 0)
        errors = result.get("errors", [])

        overlap_removed = total_scraped - unique_count

        # Add diagnostic info if scraping failed
        if not stocks and not errors:
            errors.append("No stocks found. Check ChromeDriver installation and network connectivity.")
        if errors:
            logger.error(f"Scraping errors: {errors}")

        logger.info(
            f"Scraping completed: {total_scraped} total, "
            f"{overlap_removed} overlaps removed, {unique_count} unique stocks"
        )

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
            total_found=total_scraped,
            unique_stocks=unique_count,
            overlap_removed=overlap_removed,
            new_candidates=new_candidates,
            duplicates_skipped=duplicates_skipped,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error in scrape_chartink: {e}")
        return ScrapeResponse(
            success=False,
            total_found=0,
            unique_stocks=0,
            overlap_removed=0,
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
    # Phase analysis fields
    phase: int | None = None
    status_label: str | None = None
    ath_value: float | None = None
    ath_date: str | None = None
    ema_200: float | None = None
    distance_from_ath: float | None = None
    last_analyzed: str | None = None


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
                   distance_from_high, scraped_at,
                   phase, status_label, ath_value, ath_date,
                   ema_200, distance_from_ath, last_analyzed
            FROM candidates
            ORDER BY phase DESC, scraped_at DESC
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
                scraped_at=row["scraped_at"],
                phase=row["phase"],
                status_label=row["status_label"],
                ath_value=row["ath_value"],
                ath_date=row["ath_date"],
                ema_200=row["ema_200"],
                distance_from_ath=row["distance_from_ath"],
                last_analyzed=row["last_analyzed"]
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

        # Run ATH analysis immediately
        analyzer = ATHAnalyzer()
        analysis_result = analyzer.analyze_symbol(symbol)

        if analysis_result:
            # Update watchlist with analysis data
            cursor.execute("""
                UPDATE watchlist
                SET phase = ?,
                    status_label = ?,
                    ath_value = ?,
                    ath_date = ?,
                    ema_200 = ?,
                    distance_from_ath = ?,
                    last_analyzed = ?
                WHERE symbol = ?
            """, (
                analysis_result['phase'],
                analysis_result['status_label'],
                analysis_result['ath_value'],
                analysis_result['ath_date'],
                analysis_result['ema_200'],
                analysis_result['distance_from_ath'],
                analysis_result['last_analyzed'],
                symbol
            ))
            conn.commit()

        conn.close()

        logger.info(f"Added {symbol} to watchlist with analysis")

        return AddToWatchlistResponse(
            success=True,
            analysis=analysis_result
        )

    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        return AddToWatchlistResponse(
            success=False,
            error=str(e)
        )


class AnalyzeWatchlistResponse(BaseModel):
    """Response model for analyze watchlist operation"""
    success: bool
    analyzed: int
    phase_1: int
    phase_2: int
    phase_3: int
    errors: List[str] = []


class AnalyzeCandidatesResponse(BaseModel):
    """Response model for candidates analysis"""
    success: bool
    analyzed: int
    phase_1: int
    phase_2: int
    phase_3: int
    errors: List[str] = []


class BulkAddRequest(BaseModel):
    """Request model for bulk add to watchlist"""
    symbols: List[str]


class BulkAddResponse(BaseModel):
    """Response model for bulk add to watchlist"""
    success: bool
    added: int
    skipped: int
    errors: List[str] = []


@router.post("/scanner/analyze-watchlist")
async def analyze_watchlist(x_session_id: str = Header(alias="X-Session-ID")) -> AnalyzeWatchlistResponse:
    """
    Run ATH analysis on all watchlist stocks.

    Analyzes each stock in the watchlist to determine:
    - Current phase (1, 2, or 3)
    - Status label (human-readable)
    - ATH metrics (value, date, distance)
    - EMA 200 value

    Args:
        x_session_id: Session ID from header for authentication

    Returns:
        AnalyzeWatchlistResponse with phase distribution
    """
    if not session_manager.validate_session(x_session_id):
        return AnalyzeWatchlistResponse(
            success=False,
            analyzed=0,
            phase_1=0,
            phase_2=0,
            phase_3=0,
            errors=["Not authenticated"]
        )

    try:
        logger.info("Starting watchlist analysis...")

        conn = get_db()
        cursor = conn.cursor()

        # Get all watchlist symbols
        cursor.execute("SELECT symbol FROM watchlist")
        rows = cursor.fetchall()
        symbols = [row["symbol"] for row in rows]

        logger.info(f"Analyzing {len(symbols)} watchlist stocks...")

        # Run analysis
        analyzer = ATHAnalyzer()
        results = analyzer.analyze_multiple(symbols)

        # Count phases
        phase_counts = {1: 0, 2: 0, 3: 0}
        analyzed_count = 0
        errors = []

        # Update database with results
        for symbol, result in results.items():
            if result:
                cursor.execute("""
                    UPDATE watchlist
                    SET phase = ?,
                        status_label = ?,
                        ath_value = ?,
                        ath_date = ?,
                        ema_200 = ?,
                        distance_from_ath = ?,
                        data_as_of_date = ?,
                        last_analyzed = ?
                    WHERE symbol = ?
                """, (
                    result['phase'],
                    result['status_label'],
                    result['ath_value'],
                    result['ath_date'],
                    result['ema_200'],
                    result['distance_from_ath'],
                    result.get('data_as_of_date'),  # NEW: Store data freshness
                    result['last_analyzed'],
                    symbol
                ))

                phase_counts[result['phase']] = phase_counts.get(result['phase'], 0) + 1
                analyzed_count += 1
            else:
                errors.append(f"Failed to analyze {symbol}")

        conn.commit()
        conn.close()

        logger.info(
            f"Analysis complete: {analyzed_count} analyzed, "
            f"Phase 1: {phase_counts[1]}, Phase 2: {phase_counts[2]}, Phase 3: {phase_counts[3]}"
        )

        return AnalyzeWatchlistResponse(
            success=True,
            analyzed=analyzed_count,
            phase_1=phase_counts[1],
            phase_2=phase_counts[2],
            phase_3=phase_counts[3],
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error analyzing watchlist: {e}")
        return AnalyzeWatchlistResponse(
            success=False,
            analyzed=0,
            phase_1=0,
            phase_2=0,
            phase_3=0,
            errors=[str(e)]
        )


@router.post("/scanner/analyze-candidates")
async def analyze_candidates(x_session_id: str = Header(alias="X-Session-ID")) -> AnalyzeCandidatesResponse:
    """
    Run ATH analysis on all candidate stocks.

    Similar to analyze-watchlist but operates on candidates table.
    Updates candidates with phase, status_label, ATH metrics.

    Args:
        x_session_id: Session ID from header for authentication

    Returns:
        AnalyzeCandidatesResponse with phase distribution
    """
    if not session_manager.validate_session(x_session_id):
        return AnalyzeCandidatesResponse(
            success=False,
            analyzed=0,
            phase_1=0,
            phase_2=0,
            phase_3=0,
            errors=["Not authenticated"]
        )

    try:
        logger.info("Starting candidates analysis...")

        conn = get_db()
        cursor = conn.cursor()

        # Get all candidate symbols (distinct)
        cursor.execute("SELECT DISTINCT symbol FROM candidates")
        rows = cursor.fetchall()
        symbols = [row["symbol"] for row in rows]

        logger.info(f"Analyzing {len(symbols)} candidate stocks...")

        # Run analysis
        analyzer = ATHAnalyzer()
        results = analyzer.analyze_multiple(symbols)

        # Count phases
        phase_counts = {1: 0, 2: 0, 3: 0}
        analyzed_count = 0
        errors = []

        # Update ALL rows for each symbol (since symbol can appear multiple times)
        for symbol, result in results.items():
            if result:
                cursor.execute("""
                    UPDATE candidates
                    SET phase = ?,
                        status_label = ?,
                        ath_value = ?,
                        ath_date = ?,
                        ema_200 = ?,
                        distance_from_ath = ?,
                        last_analyzed = ?
                    WHERE symbol = ?
                """, (
                    result['phase'],
                    result['status_label'],
                    result['ath_value'],
                    result['ath_date'],
                    result['ema_200'],
                    result['distance_from_ath'],
                    result['last_analyzed'],
                    symbol
                ))

                phase_counts[result['phase']] = phase_counts.get(result['phase'], 0) + 1
                analyzed_count += 1
            else:
                errors.append(f"Failed to analyze {symbol}")

        conn.commit()
        conn.close()

        logger.info(
            f"Candidates analysis complete: {analyzed_count} analyzed, "
            f"Phase 1: {phase_counts[1]}, Phase 2: {phase_counts[2]}, Phase 3: {phase_counts[3]}"
        )

        return AnalyzeCandidatesResponse(
            success=True,
            analyzed=analyzed_count,
            phase_1=phase_counts[1],
            phase_2=phase_counts[2],
            phase_3=phase_counts[3],
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error analyzing candidates: {e}")
        return AnalyzeCandidatesResponse(
            success=False,
            analyzed=0,
            phase_1=0,
            phase_2=0,
            phase_3=0,
            errors=[str(e)]
        )


@router.post("/scanner/candidates/bulk-add-to-watchlist")
async def bulk_add_to_watchlist(
    request: BulkAddRequest,
    x_session_id: str = Header(alias="X-Session-ID")
) -> BulkAddResponse:
    """
    Move multiple candidates to watchlist at once.

    Does NOT run analysis (assumes already analyzed).
    Simply moves candidates to watchlist with their phase data.

    Args:
        request: BulkAddRequest with list of symbols
        x_session_id: Session ID from header for authentication

    Returns:
        BulkAddResponse with counts and any errors
    """
    if not session_manager.validate_session(x_session_id):
        return BulkAddResponse(
            success=False,
            added=0,
            skipped=0,
            errors=["Not authenticated"]
        )

    try:
        conn = get_db()
        cursor = conn.cursor()

        added_count = 0
        skipped_count = 0
        errors = []

        for symbol in request.symbols:
            try:
                # Check if already in watchlist
                cursor.execute("SELECT 1 FROM watchlist WHERE symbol = ?", (symbol,))
                if cursor.fetchone():
                    skipped_count += 1
                    continue

                # Get candidate data including phase
                cursor.execute("""
                    SELECT phase, status_label, ath_value, ath_date,
                           ema_200, distance_from_ath, last_analyzed
                    FROM candidates
                    WHERE symbol = ?
                    LIMIT 1
                """, (symbol,))

                row = cursor.fetchone()
                if not row:
                    errors.append(f"{symbol} not found in candidates")
                    continue

                # Insert into watchlist with phase data
                cursor.execute("""
                    INSERT INTO watchlist (
                        symbol, name, type,
                        phase, status_label, ath_value, ath_date,
                        ema_200, distance_from_ath, last_analyzed
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, "", "EQUITY",
                    row["phase"], row["status_label"],
                    row["ath_value"], row["ath_date"],
                    row["ema_200"], row["distance_from_ath"],
                    row["last_analyzed"]
                ))

                # Delete from candidates (all rows with this symbol)
                cursor.execute("DELETE FROM candidates WHERE symbol = ?", (symbol,))

                added_count += 1

            except Exception as e:
                errors.append(f"Error adding {symbol}: {str(e)}")

        conn.commit()
        conn.close()

        logger.info(f"Bulk add complete: {added_count} added, {skipped_count} skipped")

        return BulkAddResponse(
            success=True,
            added=added_count,
            skipped=skipped_count,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error in bulk add: {e}")
        return BulkAddResponse(
            success=False,
            added=0,
            skipped=0,
            errors=[str(e)]
        )


@router.get("/scanner/data-freshness")
async def check_data_freshness(x_session_id: str = Header(alias="X-Session-ID")) -> DataFreshnessResponse:
    """
    Check overall data freshness across watchlist stocks.

    Samples first 10 stocks from watchlist and checks how old their CSV data is.
    This helps users understand if analysis results may be based on stale data.

    Args:
        x_session_id: Session ID from header for authentication

    Returns:
        DataFreshnessResponse with freshness summary
    """
    if not session_manager.validate_session(x_session_id):
        return DataFreshnessResponse(
            all_fresh=False,
            oldest_data_date=None,
            oldest_days=999,
            sample_size=0,
            warning="Not authenticated"
        )

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT symbol FROM watchlist LIMIT 10")
        rows = cursor.fetchall()
        symbols = [row["symbol"] for row in rows]
        conn.close()

        if not symbols:
            return DataFreshnessResponse(
                all_fresh=True,
                oldest_data_date=None,
                oldest_days=0,
                sample_size=0,
                warning=None
            )

        # Check freshness for sample stocks
        analyzer = ATHAnalyzer()
        freshness_results = []

        for symbol in symbols:
            freshness = analyzer.validate_data_freshness(symbol)
            if freshness.get('last_data_date'):  # Only include if valid
                freshness_results.append(freshness)

        if not freshness_results:
            return DataFreshnessResponse(
                all_fresh=False,
                oldest_data_date=None,
                oldest_days=999,
                sample_size=0,
                warning="Unable to check data freshness"
            )

        # Calculate summary statistics
        oldest_days = max(f['days_old'] for f in freshness_results)
        oldest_date = min(f['last_data_date'] for f in freshness_results)
        all_fresh = all(f['is_fresh'] for f in freshness_results)

        warning = None
        if not all_fresh:
            warning = f"Data is {oldest_days} days old (last updated: {oldest_date})"

        logger.info(f"Data freshness check: {sample_size} stocks, oldest: {oldest_days} days")

        return DataFreshnessResponse(
            all_fresh=all_fresh,
            oldest_data_date=oldest_date,
            oldest_days=oldest_days,
            sample_size=len(freshness_results),
            warning=warning
        )

    except Exception as e:
        logger.error(f"Error checking data freshness: {e}")
        return DataFreshnessResponse(
            all_fresh=False,
            oldest_data_date=None,
            oldest_days=999,
            sample_size=0,
            warning=f"Error: {str(e)}"
        )
