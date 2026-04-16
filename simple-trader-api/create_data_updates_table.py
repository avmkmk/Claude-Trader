"""
Database Migration: Create data_updates Table

Run this once to create the metadata tracking table.
"""

import sqlite3
import os

DB_PATH = 'data/dashboard.db'

def create_table():
    """Create data_updates table with indexes"""
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_updates (
            symbol TEXT PRIMARY KEY,
            last_updated_date DATE NOT NULL,
            last_run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'pending')),
            error_message TEXT
        )
    """)

    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_status ON data_updates(status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_last_updated ON data_updates(last_updated_date)"
    )

    conn.commit()
    conn.close()

    print(f"[OK] data_updates table created in {DB_PATH}")

if __name__ == "__main__":
    create_table()
