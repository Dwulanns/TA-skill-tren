"""
Admin Dependencies - JWT Token Verification
=============================================

Dependency functions for admin authentication and authorization.
"""

from fastapi import Depends, HTTPException, status, Header
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_auth import decode_token
from database.connection import SessionLocal
from database.models import Admin


async def get_current_admin(authorization: str = Header(...)) -> Admin:
    """
    Verify JWT token and return current admin user.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        Admin: The authenticated admin user
        
    Raises:
        HTTPException: If token is invalid or admin not found
    """
    try:
        # Extract token from "Bearer <token>"
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get admin from database
        db = SessionLocal()
        try:
            admin = db.query(Admin).filter(Admin.email == email).first()
            
            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Admin not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not admin.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin account is inactive",
                )
            
            return admin
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify token",
            headers={"WWW-Authenticate": "Bearer"},
        )
