"""
Authentication and Session Management

Provides in-memory session management for API authentication.
Sessions are created on login and validated on protected endpoints.
"""

import secrets
import time
from typing import Optional
from app.config import settings


class SessionManager:
    """
    Manages user sessions for API authentication.
    
    Sessions are stored in-memory and expire after a configured duration.
    Note: Sessions are lost on server restart.
    """
    
    def __init__(self):
        # Dictionary to store active sessions
        # Key: session_id, Value: dict with created_at and authenticated flag
        self._sessions: dict[str, dict] = {}
    
    
    def create_session(self) -> str:
        """
        Create a new authenticated session.
        
        Returns:
            str: A cryptographically secure session ID
        """
        # Generate a secure random session ID (32 bytes of randomness)
        session_id = secrets.token_urlsafe(32)
        
        # Store session with creation timestamp
        self._sessions[session_id] = {
            "created_at": time.time(),
            "authenticated": True
        }
        
        return session_id
    
    
    def validate_session(self, session_id: Optional[str]) -> bool:
        """
        Validate if a session ID is active and not expired.
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            bool: True if session is valid and active, False otherwise
        """
        # Reject empty or None session IDs
        if not session_id:
            return False
        
        # Check if session exists
        if session_id not in self._sessions:
            return False
        
        # Get session data
        session = self._sessions[session_id]
        
        # Check if session has expired
        if time.time() - session["created_at"] > settings.SESSION_EXPIRE_SECONDS:
            # Clean up expired session
            del self._sessions[session_id]
            return False
        
        return True
    
    
    def delete_session(self, session_id: str) -> bool:
        """
        Manually invalidate a session (logout).
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            bool: True if session was deleted, False if it didn't exist
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# Global session manager instance
session_manager = SessionManager()


def verify_mpin(mpin: str) -> bool:
    """
    Verify if the provided MPIN matches the configured MPIN.
    
    Args:
        mpin: The MPIN to verify
        
    Returns:
        bool: True if MPIN is correct, False otherwise
    """
    # Fail if no MPIN is configured
    if not settings.NUBRA_MPIN:
        return False
    
    # Simple string comparison (consider hashing in production)
    return mpin == settings.NUBRA_MPIN
