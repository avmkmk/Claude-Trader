"""
Quick test to verify CSV append functionality works correctly
"""
import os
import pandas as pd
from datetime import datetime, timedelta

# Test append to a sample CSV
test_csv = "../../SimpleTraderExternal/data/daily/eod2/RELIANCE.csv"

print("Testing CSV append functionality...")
print("=" * 60)

# Read existing CSV
if os.path.exists(test_csv):
    df_original = pd.read_csv(test_csv)
    print(f"\n1. Original CSV has {len(df_original)} rows")
    print(f"   Last date: {df_original['Date'].iloc[-1]}")
    print(f"   Sample data:\n{df_original.tail(3)}")

    # Get the last date
    last_date = pd.to_datetime(df_original['Date'].iloc[-1])
    next_date = last_date + timedelta(days=1)

    # Create test data to append
    test_data = pd.DataFrame({
        'Date': [next_date.strftime('%Y-%m-%d')],
        'Open': [2500.0],
        'High': [2550.0],
        'Low': [2490.0],
        'Close': [2520.0],
        'Volume': [5000000]
    })

    print(f"\n2. Appending test data:\n{test_data}")

    # Append to CSV
    test_data.to_csv(test_csv, mode='a', header=False, index=False)

    # Verify append
    df_after = pd.read_csv(test_csv)
    print(f"\n3. After append: {len(df_after)} rows")
    print(f"   Last date: {df_after['Date'].iloc[-1]}")
    print(f"   Sample data:\n{df_after.tail(3)}")

    # Check if data was appended correctly
    if len(df_after) == len(df_original) + 1:
        print("\nSUCCESS: Data appended correctly!")
        print(f"  Original rows: {len(df_original)}")
        print(f"  After append: {len(df_after)}")
        print(f"  New rows added: 1")
    else:
        print("\nERROR: Append failed!")
        print(f"  Expected: {len(df_original) + 1} rows")
        print(f"  Got: {len(df_after)} rows")

    # Rollback the test (remove the test row)
    print("\n4. Rolling back test data...")
    df_original.to_csv(test_csv, index=False)
    print("   Test data removed")

else:
    print(f"ERROR: CSV file not found at {test_csv}")

print("\n" + "=" * 60)
print("Append test complete!")
