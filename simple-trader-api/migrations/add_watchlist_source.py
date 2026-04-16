"""
Migration: Add source tracking to watchlist table
"""
import sqlite3
from datetime import datetime
import os

# Get the correct path to database
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'dashboard.db')

def migrate():
    """Add source, source_metadata, and data_as_of_date columns to watchlist."""

    print(f"Migrating database at: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Backup current data
        print("Backing up watchlist table...")
        cursor.execute("DROP TABLE IF EXISTS watchlist_backup")
        cursor.execute("CREATE TABLE watchlist_backup AS SELECT * FROM watchlist")

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(watchlist)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add new columns if they don't exist
        if 'source' not in columns:
            print("Adding 'source' column...")
            cursor.execute("ALTER TABLE watchlist ADD COLUMN source TEXT DEFAULT 'manual'")

        if 'source_metadata' not in columns:
            print("Adding 'source_metadata' column...")
            cursor.execute("ALTER TABLE watchlist ADD COLUMN source_metadata TEXT DEFAULT NULL")

        if 'data_as_of_date' not in columns:
            print("Adding 'data_as_of_date' column...")
            cursor.execute("ALTER TABLE watchlist ADD COLUMN data_as_of_date TEXT DEFAULT NULL")

        # Create index on source for filtering
        print("Creating index on source column...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_source ON watchlist(source)")

        # Update existing rows to have default source
        print("Updating existing rows...")
        cursor.execute("UPDATE watchlist SET source = 'manual' WHERE source IS NULL")

        conn.commit()

        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM watchlist")
        count = cursor.fetchone()[0]
        print(f"\nMigration complete!")
        print(f"   - {count} rows in watchlist table")
        print(f"   - Backup saved as 'watchlist_backup'")

        # Show sample data
        cursor.execute("SELECT symbol, source, data_as_of_date FROM watchlist LIMIT 3")
        samples = cursor.fetchall()
        if samples:
            print(f"\n   Sample data:")
            for symbol, source, data_date in samples:
                print(f"     - {symbol}: source={source}, data_as_of={data_date}")

        return True

    except Exception as e:
        print(f"\nMigration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
