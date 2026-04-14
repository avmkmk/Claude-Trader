"""
Add phase analysis columns to candidates table
"""
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "dashboard.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add phase columns (same as watchlist)
        cursor.execute("ALTER TABLE candidates ADD COLUMN phase INTEGER DEFAULT NULL")
        cursor.execute("ALTER TABLE candidates ADD COLUMN status_label TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE candidates ADD COLUMN ath_value REAL DEFAULT NULL")
        cursor.execute("ALTER TABLE candidates ADD COLUMN ath_date TEXT DEFAULT NULL")
        cursor.execute("ALTER TABLE candidates ADD COLUMN ema_200 REAL DEFAULT NULL")
        cursor.execute("ALTER TABLE candidates ADD COLUMN distance_from_ath REAL DEFAULT NULL")
        cursor.execute("ALTER TABLE candidates ADD COLUMN last_analyzed TIMESTAMP DEFAULT NULL")

        conn.commit()
        print("[OK] Migration complete: Phase columns added to candidates table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("[WARN] Phase columns already exist in candidates table")
        else:
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
