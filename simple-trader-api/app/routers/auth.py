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
    phone: str
    """Phone number registered with broker"""
    mpin: str
    """Broker MPIN"""
    otp: str
    """OTP received on phone"""


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
    Authenticate with Nubra broker using phone, MPIN, and OTP.

    This creates a persistent Nubra session that will be used for:
    - Historical data fetching
    - Real-time market data
    - Order placement
    - Portfolio management

    The session persists for several days and doesn't require re-authentication.

    Args:
        request: NubraLoginRequest with phone, mpin, and otp

    Returns:
        NubraLoginResponse: Success status, session ID, and message
    """
    try:
        # Add parent directory to path to import apis module
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from apis.nubra_api import NubraAPIHandler
        from nubra_python_sdk.start_sdk import NubraEnv

        # Create handler and authenticate
        handler = NubraAPIHandler(env=NubraEnv.PROD)
        success, error = handler.initialize_sdk_with_credentials(
            phone=request.phone,
            mpin=request.mpin,
            otp=request.otp
        )

        if success:
            # Create session for authenticated user
            session_id = session_manager.create_session()

            # Test the connection with a simple data fetch
            test_df = handler.get_historical_data('RELIANCE', '2026-04-14', '2026-04-15', '1d')

            return NubraLoginResponse(
                success=True,
                session_id=session_id,
                message="Successfully authenticated with Nubra. Session will persist for several days."
            )
        else:
            return NubraLoginResponse(
                success=False,
                message=f"Authentication failed: {error}"
            )

    except Exception as e:
        return NubraLoginResponse(
            success=False,
            message=f"Error during authentication: {str(e)}"
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

        from apis.nubra_api import NubraAPIHandler
        from nubra_python_sdk.start_sdk import NubraEnv

        # Try to initialize SDK (will use saved token if available)
        handler = NubraAPIHandler(env=NubraEnv.PROD)
        success = handler.initialize_sdk()

        if success:
            # Test with a simple data fetch
            test_df = handler.get_historical_data('RELIANCE', '2026-04-14', '2026-04-15', '1d')

            if test_df is not None:
                return NubraStatusResponse(
                    authenticated=True,
                    message="Nubra SDK is authenticated and working"
                )
            else:
                return NubraStatusResponse(
                    authenticated=False,
                    message="Nubra SDK initialized but data fetch failed. May need re-authentication."
                )
        else:
            return NubraStatusResponse(
                authenticated=False,
                message="Nubra SDK not authenticated. Please login with phone/MPIN/OTP."
            )

    except Exception as e:
        return NubraStatusResponse(
            authenticated=False,
            message=f"Error checking Nubra status: {str(e)}"
        )
