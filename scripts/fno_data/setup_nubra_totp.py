"""
Nubra TOTP Setup - One-Time Interactive Setup
==============================================
Sets up TOTP authentication so future scripts can log in automatically
without requiring OTP each time.

USAGE (exact command - must use -X utf8 on Windows):
    python -X utf8 scripts/fno_data/setup_nubra_totp.py

PREREQUISITES:
    Set these OS environment variables BEFORE running:
    
    Windows (CMD):
        set PHONE_NO=your_phone_number
        set MPIN=your_mpin
    
    Windows (PowerShell):
        $env:PHONE_NO="your_phone_number"
        $env:MPIN="your_mpin"
    
    Or set permanently via System Properties → Environment Variables.

WHAT IT DOES:
    1. Generates a TOTP secret
    2. Shows the secret for you to add to Google Authenticator/Authy
    3. Enables TOTP on your Nubra account
    4. Verifies TOTP login works
    5. Saves the secret to .env for reference

AFTER SETUP:
    python -X utf8 scripts/fno_data/runner.py --step 2
"""

import sys
import os
import io
import re

# ─── Fix Windows encoding (must happen before any SDK import) ─────────
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def banner(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_env_vars():
    """Check that required OS environment variables are set."""
    phone = os.environ.get('PHONE_NO', '').strip()
    mpin = os.environ.get('MPIN', '').strip()

    if not phone:
        print("ERROR: PHONE_NO environment variable is not set.")
        print()
        print("Set it before running this script:")
        print('  CMD:       set PHONE_NO=your_phone_number')
        print('  PowerShell: $env:PHONE_NO="your_phone_number"')
        print('  Permanent:  System Properties → Environment Variables')
        sys.exit(1)

    if not mpin:
        print("ERROR: MPIN environment variable is not set.")
        print()
        print("Set it before running this script:")
        print('  CMD:       set MPIN=your_mpin')
        print('  PowerShell: $env:MPIN="your_mpin"')
        sys.exit(1)

    return phone, mpin


def step1_generate_secret():
    """Generate a new TOTP secret."""
    banner("STEP 1: Generate TOTP Secret")

    import json
    from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv

    print("Connecting to Nubra PROD...")
    print("You will be prompted for:")
    print("  1. OTP (sent to your phone)")
    print("  2. MPIN")
    print()

    client = InitNubraSdk(NubraEnv.PROD, env_creds=True)

    print("Generating TOTP secret...")
    raw_response = client.totp_generate_secret()

    # Parse the JSON response
    # Format: {"data": {"secret_key": "...", "qr_image": "data:image/png;base64,..."}, "message": "..."}
    try:
        resp = json.loads(raw_response)
        secret = resp["data"]["secret_key"]
        qr_b64 = resp["data"]["qr_image"]
        # Strip the "data:image/png;base64," prefix
        qr_base64_data = qr_b64.split(",", 1)[1] if "," in qr_b64 else qr_b64
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse TOTP response as JSON: {e}")
        print(f"Raw response: {raw_response}")
        print()
        # Fallback: use raw response as secret
        secret = raw_response.strip().strip('"')
        qr_base64_data = None

    return client, secret, qr_base64_data


def step2_show_secret(secret, phone, qr_base64_data):
    """Display the TOTP secret and save QR code for easy scanning."""
    banner("STEP 2: Add Secret to Authenticator")

    import base64

    qr_path = PROJECT_ROOT / "nubra_totp_qr.png"

    # Save QR code from the base64 image returned by Nubra API
    if qr_base64_data:
        try:
            qr_bytes = base64.b64decode(qr_base64_data)
            qr_path.write_bytes(qr_bytes)
            print(f"QR Code saved to: {qr_path}")

            # Try to open the image automatically on Windows
            try:
                os.startfile(str(qr_path))
                print(f"Opened QR code in your default image viewer.")
            except Exception:
                pass
        except Exception as e:
            print(f"Could not save QR image: {e}")
            qr_base64_data = None

    if not qr_base64_data:
        # Fallback: generate QR from otpauth URI
        try:
            import qrcode
            import urllib.parse
            otpauth_uri = (
                f"otpauth://totp/Nubra:{phone}"
                f"?secret={secret}"
                f"&issuer=Nubra"
                f"&algorithm=SHA1"
                f"&digits=6"
                f"&period=30"
            )
            qr_img = qrcode.make(otpauth_uri)
            qr_img.save(str(qr_path))
            print(f"QR Code saved to: {qr_path}")
            try:
                os.startfile(str(qr_path))
                print(f"Opened QR code in your default image viewer.")
            except Exception:
                pass
        except ImportError:
            print("Install qrcode: pip install qrcode[pil]")

    print()
    print(f"Your TOTP Secret: {secret}")
    print()
    print("Instructions:")
    print("  1. Scan the QR image with Google Authenticator (or Authy)")
    print("  OR manually add the key:")
    print(f"     Account: Nubra ({phone})")
    print(f"     Key:     {secret}")
    print(f"     Type:    Time-based (TOTP)")
    print()

    input("Press Enter after you have added the secret to your authenticator... ")


def step3_enable_totp(client):
    """Enable TOTP on the account."""
    banner("STEP 3: Enable TOTP")

    print("You will be prompted for:")
    print("  1. TOTP code (from your authenticator app)")
    print("  2. MPIN")
    print()

    client.totp_enable()
    print("TOTP enabled successfully!")


def step4_verify_login():
    """Verify that TOTP login works."""
    banner("STEP 4: Verify TOTP Login")

    from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv

    print("Testing TOTP login...")
    print("You will be prompted for:")
    print("  1. TOTP code (from your authenticator app)")
    print("  2. MPIN")
    print()

    client = InitNubraSdk(NubraEnv.PROD, totp_login=True, env_creds=True)

    # Quick sanity check - fetch something
    from nubra_python_sdk.marketdata.market_data import MarketData
    md = MarketData(client)

    print("TOTP login verified successfully!")
    return True


def step5_save_secret(secret):
    """Save the TOTP secret to .env for reference."""
    banner("STEP 5: Save Secret to .env")

    env_path = PROJECT_ROOT / ".env"

    if env_path.exists():
        content = env_path.read_text(encoding='utf-8')

        # Check if TOTP_SECRET already exists
        if 'TOTP_SECRET' in content:
            content = re.sub(
                r'^TOTP_SECRET=.*$',
                f'TOTP_SECRET="{secret}"',
                content,
                flags=re.MULTILINE
            )
        else:
            content += f'\n# Nubra TOTP Secret (for reference)\nTOTP_SECRET="{secret}"\n'

        env_path.write_text(content, encoding='utf-8')
        print(f"Updated {env_path}")
    else:
        env_path.write_text(f'TOTP_SECRET="{secret}"\n', encoding='utf-8')
        print(f"Created {env_path}")

    print(f"TOTP_SECRET saved: {secret[:8]}...")


def main():
    banner("NUBRA TOTP SETUP")

    print("This script sets up TOTP authentication for Nubra API.")
    print("You only need to run this ONCE.")
    print()

    # Check environment variables
    phone, mpin = check_env_vars()
    print(f"Phone: {phone[:4]}****")
    print(f"MPIN:  ****")

    # Confirm
    print()
    proceed = input("Continue with TOTP setup? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Aborted.")
        return

    # Step 1: Generate secret (also does initial OTP login)
    client, secret, qr_base64_data = step1_generate_secret()

    # Step 2: Show secret + QR code, wait for user
    step2_show_secret(secret, phone, qr_base64_data)

    # Step 3: Enable TOTP
    step3_enable_totp(client)

    # Step 4: Verify
    try:
        step4_verify_login()
    except Exception as e:
        print(f"\nVerification failed: {e}")
        print("TOTP may still be enabled. Try logging in manually.")

    # Step 5: Save
    step5_save_secret(secret)

    # Clean up QR image (security - don't leave secret on disk as image)
    qr_path = PROJECT_ROOT / "nubra_totp_qr.png"
    if qr_path.exists():
        try:
            qr_path.unlink()
            print(f"Cleaned up QR image: {qr_path}")
        except Exception:
            print(f"Please delete manually: {qr_path}")

    banner("SETUP COMPLETE")
    print("You can now run the data pipeline with:")
    print()
    print("  python -X utf8 scripts/fno_data/runner.py --step 2")
    print()


if __name__ == '__main__':
    main()
