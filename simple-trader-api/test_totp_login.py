"""
Test TOTP (Authenticator App) Login for Nubra
"""
import os
import sys
sys.path.insert(0, '..')

from apis.nubra_api import NubraAPIHandler
from nubra_python_sdk.start_sdk import NubraEnv, InitNubraSdk
from nubra_python_sdk.marketdata.market_data import MarketData

print("=" * 60)
print("Testing TOTP Authenticator Login")
print("=" * 60)

phone = os.getenv('PHONE_NO')
mpin = os.getenv('MPIN')

if not phone or not mpin:
    print("ERROR: PHONE_NO and MPIN must be set in environment variables")
    sys.exit(1)

print(f"\nPhone: {phone[:3]}XXXXX{phone[-2:]}")
print("MPIN: ******")

# Get TOTP from user's authenticator app
totp = input("\nEnter TOTP code from your authenticator app (6 digits): ").strip()

if not totp or len(totp) != 6:
    print("ERROR: TOTP must be 6 digits")
    sys.exit(1)

# Set TOTP in environment
os.environ['TOTP'] = totp

print("\nAuthenticating with TOTP...")
try:
    # Initialize SDK with TOTP login
    sdk = InitNubraSdk(NubraEnv.PROD, totp_login=True, env_creds=True)
    market_data = MarketData(sdk)

    print("\n" + "=" * 60)
    print("SUCCESS! TOTP Authentication Complete")
    print("=" * 60)

    # Test data fetch
    print("\nTesting data fetch...")
    from datetime import datetime, timedelta

    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    df = market_data.historical_data(
        exchange="NSE",
        symbol="RELIANCE",
        from_datetime=yesterday,
        to_datetime=today,
        interval="1d"
    )

    if df and len(df) > 0:
        print(f"SUCCESS: Fetched {len(df)} rows of data")
        print("\nSample data:")
        print(df.head())
    else:
        print("No data returned (market might be closed)")

    print("\n" + "=" * 60)
    print("Your TOTP session is now saved!")
    print("You can now run the data pipeline without entering TOTP:")
    print("  python update_daily_data.py")
    print("=" * 60)

except Exception as e:
    print("\n" + "=" * 60)
    print("FAILED: TOTP Authentication Failed")
    print("=" * 60)
    print(f"\nError: {str(e)}")
    print("\nPlease check:")
    print("  1. TOTP code is current (refreshes every 30 seconds)")
    print("  2. Authenticator app is synced with server time")
    print("  3. Phone number and MPIN are correct")
    sys.exit(1)
