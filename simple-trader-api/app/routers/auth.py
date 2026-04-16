"""
Authentication Endpoints

Provides login, logout, and session status endpoints for API authentication.
All protected endpoints require a valid session ID in the X-Session-ID header.
"""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.auth import session_manager, verify_mpin
from app.config import settings
import sys
import os


# Create router with /auth prefix
router = APIRouter(prefix="/auth", tags=["auth"])


# Request/Response Models

class LoginRequest(BaseModel):
    """Request model for login endpoint"""
    mpin: str
    """User's MPIN for authentication"""


class LoginResponse(BaseModel):
    """Response model for login endpoint"""
    success: bool
    """Whether login was successful"""
    session_id: str | None = None
    """Session ID if login successful, None otherwise"""
    message: str | None = None
    """Error message if login failed"""


class StatusResponse(BaseModel):
    """Response model for status endpoint"""
    authenticated: bool
    """Whether the session is currently authenticated"""


class NubraLoginRequest(BaseModel):
    """Request model for Nubra broker authentication"""
    totp: str
    """TOTP code from authenticator app (6 digits)"""


class NubraLoginResponse(BaseModel):
    """Response model for Nubra login endpoint"""
    success: bool
    """Whether authentication was successful"""
    session_id: str | None = None
    """Session ID if login successful"""
    message: str | None = None
    """Error or success message"""


class NubraStatusResponse(BaseModel):
    """Response model for Nubra status endpoint"""
    authenticated: bool
    """Whether Nubra SDK is authenticated"""
    message: str | None = None
    """Additional status information"""


# API Endpoints

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with MPIN and create a new session.
    
    Args:
        request: LoginRequest containing the user's MPIN
        
    Returns:
        LoginResponse: Success status and session ID if authenticated
    """
    # Check if MPIN is configured in the server
    if not settings.NUBRA_MPIN:
        return LoginResponse(
            success=False, 
            message="NUBRA_MPIN not set in environment variables"
        )
    
    # Verify the provided MPIN
    if verify_mpin(request.mpin):
        # Create new session on successful authentication
        session_id = session_manager.create_session()
        return LoginResponse(success=True, session_id=session_id)
    
    # Return failure for invalid MPIN
    return LoginResponse(success=False, message="Invalid MPIN")


@router.post("/logout")
async def logout(x_session_id: str = Header(alias="X-Session-ID")):
    """
    Invalidate the current session (logout).
    
    Args:
        x_session_id: Session ID from header
        
    Returns:
        dict: Success confirmation
    """
    session_manager.delete_session(x_session_id)
    return {"success": True}


@router.get("/status", response_model=StatusResponse)
async def status(x_session_id: str = Header(alias="X-Session-ID", default=None)):
    """
    Check if the current session is authenticated.

    Args:
        x_session_id: Session ID from header (optional)

    Returns:
        StatusResponse: Authentication status
    """
    authenticated = session_manager.validate_session(x_session_id)
    return StatusResponse(authenticated=authenticated)


# Nubra Broker Authentication Endpoints

@router.post("/nubra/login", response_model=NubraLoginResponse)
async def nubra_login(request: NubraLoginRequest):
    """
    Authenticate with Nubra broker using TOTP (authenticator app).

    This creates a persistent Nubra session that will be used for:
    - Historical data fetching
    - Real-time market data
    - Order placement
    - Portfolio management

    The session persists for several days and doesn't require re-authentication.

    Prerequisites:
    - PHONE_NO and MPIN must be set in server environment variables
    - User must have TOTP authenticator app (Google Authenticator, etc.)

    Args:
        request: NubraLoginRequest with totp code

    Returns:
        NubraLoginResponse: Success status, session ID, and message
    """
    try:
        # Add parent directory to path to import apis module
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from nubra_python_sdk.start_sdk import NubraEnv, InitNubraSdk
        from nubra_python_sdk.marketdata.market_data import MarketData

        # Get phone and MPIN from server environment
        phone = os.getenv('PHONE_NO')
        mpin = os.getenv('MPIN')

        if not phone or not mpin:
            return NubraLoginResponse(
                success=False,
                message="Server configuration error: PHONE_NO or MPIN not set in environment"
            )

        # Set TOTP in environment temporarily
        os.environ['TOTP'] = request.totp

        # Initialize SDK with TOTP login
        sdk_instance = InitNubraSdk(NubraEnv.PROD, totp_login=True, env_creds=True)
        market_data_api = MarketData(sdk_instance)

        # Clear TOTP from environment
        if 'TOTP' in os.environ:
            del os.environ['TOTP']

        # Test the connection with a simple data fetch
        from datetime import datetime, timedelta
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Create session for authenticated user
        session_id = session_manager.create_session()

        return NubraLoginResponse(
            success=True,
            session_id=session_id,
            message="Successfully authenticated with TOTP. Session will persist for several days."
        )

    except Exception as e:
        # Clear TOTP on error
        if 'TOTP' in os.environ:
            del os.environ['TOTP']

        error_msg = str(e)
        if "440" in error_msg or "Unauthorized" in error_msg:
            return NubraLoginResponse(
                success=False,
                message="Invalid TOTP code. Please check your authenticator app and try again."
            )
        else:
            return NubraLoginResponse(
                success=False,
                message=f"Authentication error: {error_msg}"
            )


@router.get("/nubra/status", response_model=NubraStatusResponse)
async def nubra_status():
    """
    Check if Nubra SDK is authenticated and ready to use.

    Returns:
        NubraStatusResponse: Authentication status and message
    """
    try:
        # Add parent directory to path to import apis module
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from nubra_python_sdk.start_sdk import NubraEnv, InitNubraSdk
        from nubra_python_sdk.marketdata.market_data import MarketData

        # Try to initialize SDK with TOTP (will use saved token if available)
        sdk_instance = InitNubraSdk(NubraEnv.PROD, totp_login=True, env_creds=True)
        market_data_api = MarketData(sdk_instance)

        # Test with a simple data fetch
        from datetime import datetime, timedelta
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        test_request = {
            "exchange": "NSE",
            "type": "STOCK",
            "values": ["RELIANCE"],
            "fields": ["open", "high", "low", "close", "volume"],
            "startDate": yesterday.isoformat() + "Z",
            "endDate": now.isoformat() + "Z",
            "interval": "1d"
        }

        test_df = market_data_api.historical_data(test_request)

        if test_df is not None:
            return NubraStatusResponse(
                authenticated=True,
                message="Nubra is authenticated and working with TOTP"
            )
        else:
            return NubraStatusResponse(
                authenticated=False,
                message="Nubra initialized but data fetch failed. May need re-authentication."
            )

    except Exception as e:
        error_msg = str(e)
        if "440" in error_msg or "Unauthorized" in error_msg or "Missing token" in error_msg:
            return NubraStatusResponse(
                authenticated=False,
                message="Not authenticated. Please login with TOTP code from your authenticator app."
            )
        else:
            return NubraStatusResponse(
                authenticated=False,
                message=f"Error: {error_msg}"
            )


# TOTP Setup Models
class TotpGenerateResponse(BaseModel):
    """Response model for TOTP secret generation"""
    success: bool
    secret: str | None = None
    qr_url: str | None = None
    message: str


class TotpEnableRequest(BaseModel):
    """Request model for enabling TOTP"""
    totp: str
    mpin: str


class TotpEnableResponse(BaseModel):
    """Response model for TOTP enable"""
    success: bool
    message: str


@router.post("/nubra/totp/generate-secret", response_model=TotpGenerateResponse)
async def generate_totp_secret():
    """
    Step 1: Generate TOTP secret for Nubra account.

    This must be called first to set up TOTP authentication.
    The returned secret should be added to an authenticator app
    (Google Authenticator, Authy, etc.).

    Returns:
        TotpGenerateResponse: TOTP secret and QR code URL
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv

        # Initialize SDK for setup
        setup_client = InitNubraSdk(NubraEnv.PROD)
        secret = setup_client.totp_generate_secret()

        if secret:
            # Generate QR code URL for easier setup
            # Format: otpauth://totp/Nubra:{phone}?secret={secret}&issuer=Nubra
            phone = os.getenv('PHONE_NO', 'user')
            qr_url = f"otpauth://totp/Nubra:{phone}?secret={secret}&issuer=Nubra"

            return TotpGenerateResponse(
                success=True,
                secret=secret,
                qr_url=qr_url,
                message=f"TOTP secret generated. Add this to your authenticator app: {secret}"
            )
        else:
            return TotpGenerateResponse(
                success=False,
                message="Failed to generate TOTP secret"
            )

    except Exception as e:
        return TotpGenerateResponse(
            success=False,
            message=f"Error generating TOTP secret: {str(e)}"
        )


@router.post("/nubra/totp/enable", response_model=TotpEnableResponse)
async def enable_totp(request: TotpEnableRequest):
    """
    Step 2: Enable TOTP on Nubra account.

    This must be called after generating the secret and adding it to
    your authenticator app. It verifies that TOTP is working correctly.

    Args:
        request: TotpEnableRequest with TOTP code and MPIN

    Returns:
        TotpEnableResponse: Success status and message
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv

        # Set credentials in environment
        phone = os.getenv('PHONE_NO')
        if not phone:
            return TotpEnableResponse(
                success=False,
                message="Server configuration error: PHONE_NO not set"
            )

        # Temporarily set TOTP and MPIN in environment
        os.environ['TOTP'] = request.totp
        os.environ['MPIN'] = request.mpin

        try:
            # Initialize SDK for setup
            setup_client = InitNubraSdk(NubraEnv.PROD, env_creds=True)

            # Enable TOTP - this will verify the TOTP code and MPIN
            setup_client.totp_enable()

            return TotpEnableResponse(
                success=True,
                message="TOTP enabled successfully! You can now login with TOTP."
            )
        finally:
            # Clean up environment
            if 'TOTP' in os.environ:
                del os.environ['TOTP']
            if 'MPIN' in os.environ:
                del os.environ['MPIN']

    except Exception as e:
        error_msg = str(e)
        if "Invalid" in error_msg or "incorrect" in error_msg:
            return TotpEnableResponse(
                success=False,
                message="Invalid TOTP code or MPIN. Please check and try again."
            )
        else:
            return TotpEnableResponse(
                success=False,
                message=f"Error enabling TOTP: {error_msg}"
            )
