"""
Database Migrations for ATH Monitoring System

Run this script to create the candidates table and enhance the watchlist table
with ATH analysis columns.
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "dashboard.db")


def create_candidates_table(conn: sqlite3.Connection):
    """Create candidates table for scraped stocks"""
    try:
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='candidates'
        """)

        if cursor.fetchone():
            logger.info("candidates table already exists")
            return

        # Create candidates table
        cursor.execute("""
            CREATE TABLE candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                source TEXT NOT NULL,
                current_price REAL,
                week_52_high REAL,
                distance_from_high REAL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, source)
            )
        """)

        conn.commit()
        logger.info("✓ Created candidates table")

    except Exception as e:
        logger.error(f"Error creating candidates table: {e}")
        raise


def enhance_watchlist_table(conn: sqlite3.Connection):
    """Add ATH analysis columns to watchlist table"""
    try:
        cursor = conn.cursor()

        # Get existing columns
        cursor.execute("PRAGMA table_info(watchlist)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Columns to add
        new_columns = [
            ("phase", "INTEGER DEFAULT NULL"),
            ("status_label", "TEXT DEFAULT NULL"),
            ("ath_value", "REAL DEFAULT NULL"),
            ("ath_date", "TEXT DEFAULT NULL"),
            ("ema_200", "REAL DEFAULT NULL"),
            ("distance_from_ath", "REAL DEFAULT NULL"),
            ("last_analyzed", "TIMESTAMP DEFAULT NULL")
        ]

        # Add missing columns
        added_count = 0
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE watchlist ADD COLUMN {col_name} {col_type}")
                logger.info(f"✓ Added column: {col_name}")
                added_count += 1
            else:
                logger.info(f"  Column {col_name} already exists")

        if added_count > 0:
            conn.commit()
            logger.info(f"✓ Enhanced watchlist table ({added_count} columns added)")
        else:
            logger.info("  Watchlist table already has all required columns")

    except Exception as e:
        logger.error(f"Error enhancing watchlist table: {e}")
        raise


def run_migrations():
    """Run all database migrations"""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        logger.info(f"Connected to database: {DB_PATH}")

        # Run migrations
        create_candidates_table(conn)
        enhance_watchlist_table(conn)

        conn.close()
        logger.info("✓ All migrations completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting database migrations...")
    run_migrations()
