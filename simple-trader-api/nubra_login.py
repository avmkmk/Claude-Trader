"""
Interactive Nubra Login Script
Run this once to authenticate and save your session token.
After successful login, the data pipeline will work without OTP.
"""
import os
import sys
sys.path.insert(0, '..')

from apis.nubra_api import NubraAPIHandler
from nubra_python_sdk.start_sdk import NubraEnv

print("=" * 60)
print("Nubra Interactive Login")
print("=" * 60)

# Read credentials from environment
phone = os.getenv('PHONE_NO')
mpin = os.getenv('MPIN')

if not phone or not mpin:
    print("ERROR: PHONE_NO and MPIN must be set in environment variables")
    sys.exit(1)

print(f"\nPhone Number: {phone[:3]}XXXXX{phone[-2:]}")
print("MPIN: ******")

# Request OTP
print("\nAn OTP will be sent to your phone number...")
otp = input("Enter OTP: ").strip()

if not otp:
    print("ERROR: OTP is required")
    sys.exit(1)

# Initialize SDK with credentials
print("\nAuthenticating...")
handler = NubraAPIHandler(env=NubraEnv.PROD)
success, error = handler.initialize_sdk_with_credentials(
    phone=phone,
    mpin=mpin,
    otp=otp
)

if success:
    print("\n" + "=" * 60)
    print("SUCCESS! Authentication complete")
    print("=" * 60)
    print("\nYour session token has been saved.")
    print("You can now run the data pipeline without OTP:")
    print("  python update_daily_data.py")
    print("\n" + "=" * 60)

    # Test a simple data fetch
    print("\nTesting data fetch...")
    df = handler.get_historical_data('RELIANCE', '2026-04-14', '2026-04-15', '1d')
    if df is not None and len(df) > 0:
        print(f"SUCCESS: Fetched {len(df)} rows of data")
        print("\nSample data:")
        print(df.head())
    else:
        print("WARNING: No data returned (market might be closed)")

else:
    print("\n" + "=" * 60)
    print("FAILED: Authentication failed")
    print("=" * 60)
    print(f"\nError: {error}")
    print("\nPlease check:")
    print("  1. Phone number is correct")
    print("  2. MPIN is correct")
    print("  3. OTP was entered correctly")
    print("  4. Internet connection is working")
    sys.exit(1)
