"""
Authentication Endpoints

Provides login, logout, and session status endpoints for API authentication.
All protected endpoints require a valid session ID in the X-Session-ID header.
"""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.auth import session_manager, verify_mpin
from app.config import settings


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
