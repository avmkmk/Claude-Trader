"""Tests for UpdateMetadataDB"""

import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from lib.update_metadata_db import UpdateMetadataDB

@pytest.fixture
def test_db(tmp_path):
    """Create test database"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE data_updates (
            symbol TEXT PRIMARY KEY,
            last_updated_date DATE NOT NULL,
            last_run_timestamp TIMESTAMP,
            status TEXT NOT NULL,
            error_message TEXT
        )
    """)

    # Insert test data: stock updated 3 days ago
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT INTO data_updates (symbol, last_updated_date, status)
        VALUES ('RELIANCE', ?, 'success')
    """, (three_days_ago,))

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_stocks_to_update_returns_gaps(test_db):
    """Should return stocks with data gaps"""
    db = UpdateMetadataDB(test_db)
    stocks = db.get_stocks_to_update()

    assert len(stocks) == 1
    symbol, from_date, to_date = stocks[0]
    assert symbol == 'RELIANCE'
    # from_date should be 2 days ago (last_updated + 1)
    # to_date should be today

def test_update_stock_status_success(test_db):
    """Should update date and status on success"""
    db = UpdateMetadataDB(test_db)
    today = datetime.now().strftime('%Y-%m-%d')

    db.update_stock_status('RELIANCE', today, 'success')

    # Verify update
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM data_updates WHERE symbol = 'RELIANCE'")
    row = cursor.fetchone()

    assert row['status'] == 'success'
    assert row['last_updated_date'] == today
    assert row['error_message'] is None

def test_update_stock_status_failure(test_db):
    """Should not update date on failure"""
    db = UpdateMetadataDB(test_db)
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')

    db.update_stock_status('RELIANCE', None, 'failed', 'Network timeout')

    # Verify update
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM data_updates WHERE symbol = 'RELIANCE'")
    row = cursor.fetchone()

    assert row['status'] == 'failed'
    assert row['last_updated_date'] == three_days_ago  # Unchanged
    assert row['error_message'] == 'Network timeout'

def test_get_failed_stocks(test_db):
    """Should return stocks with failed status"""
    db = UpdateMetadataDB(test_db)

    # Mark stock as failed
    db.update_stock_status('RELIANCE', None, 'failed', 'API error')

    # Get failed stocks
    failed = db.get_failed_stocks()

    assert len(failed) == 1
    symbol, from_date, to_date = failed[0]
    assert symbol == 'RELIANCE'

def test_get_run_statistics(test_db):
    """Should return correct statistics"""
    db = UpdateMetadataDB(test_db)
    today = datetime.now().strftime('%Y-%m-%d')

    # Add more test data
    cursor = db.conn.cursor()
    cursor.execute("""
        INSERT INTO data_updates (symbol, last_updated_date, status)
        VALUES ('INFY', ?, 'success')
    """, (today,))
    cursor.execute("""
        INSERT INTO data_updates (symbol, last_updated_date, status)
        VALUES ('TCS', ?, 'failed')
    """, ((datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),))
    db.conn.commit()

    stats = db.get_run_statistics()

    assert stats['total'] == 3
    assert stats['up_to_date'] == 1  # INFY
    assert stats['needs_update'] == 2  # RELIANCE, TCS
    assert stats['failed'] == 1  # TCS

def test_get_stocks_to_update_excludes_current(test_db):
    """Should not return stocks already up to date"""
    db = UpdateMetadataDB(test_db)
    today = datetime.now().strftime('%Y-%m-%d')

    # Update RELIANCE to today
    db.update_stock_status('RELIANCE', today, 'success')

    # Should return empty list
    stocks = db.get_stocks_to_update()
    assert len(stocks) == 0

def test_bootstrap_from_csvs(test_db, tmp_path):
    """Should bootstrap metadata from CSV files"""
    import pandas as pd

    db = UpdateMetadataDB(test_db)

    # Create test CSV
    csv_dir = tmp_path / "csv_data"
    csv_dir.mkdir()

    csv_path = csv_dir / "INFY.csv"
    df = pd.DataFrame({
        'Date': ['2026-01-01', '2026-01-02', '2026-01-03'],
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [99, 100, 101],
        'Close': [103, 104, 105],
        'Volume': [1000, 2000, 3000]
    })
    df.to_csv(str(csv_path), index=False)

    # Bootstrap
    db.bootstrap_from_csvs(str(csv_dir), ['INFY'])

    # Verify
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM data_updates WHERE symbol = 'INFY'")
    row = cursor.fetchone()

    assert row is not None
    assert row['symbol'] == 'INFY'
    assert row['last_updated_date'] == '2026-01-03'
    assert row['status'] == 'success'

def test_close_connection(test_db):
    """Should close database connection"""
    db = UpdateMetadataDB(test_db)
    assert db.conn is not None

    db.close()
    assert db.conn is None
