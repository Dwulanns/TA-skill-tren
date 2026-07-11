"""
Authentication Routes - Admin Login and Token Management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from database.connection import get_db
from database.models import Admin
from config_auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_wib_now,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from schemas_auth import AdminLoginRequest, AdminLoginResponse, AdminRegisterRequest
from constants import AUTH_ERROR_INVALID_CREDENTIALS, AUTH_ERROR_INACTIVE_ACCOUNT, AUTH_ERROR_EMAIL_EXISTS, AUTH_ERROR_USERNAME_EXISTS

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


def _create_admin_token(admin: Admin) -> str:
    """
    Create JWT token for admin
    
    Args:
        admin: Admin database model instance
        
    Returns:
        JWT access token string
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": admin.email, "role": "admin"},
        expires_delta=access_token_expires
    )


def _create_login_response(admin: Admin) -> AdminLoginResponse:
    """
    Create login response with token
    
    Args:
        admin: Admin database model instance
        
    Returns:
        AdminLoginResponse with token and admin info
    """
    access_token = _create_admin_token(admin)
    return AdminLoginResponse(
        access_token=access_token,
        email=admin.email,
        username=admin.username
    )


@router.post("/login", response_model=AdminLoginResponse)
async def login(
    credentials: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint - returns JWT token for authentication.
    
    Args:
        credentials: Email and password
        db: Database session
        
    Returns:
        AdminLoginResponse with access token
        
    Raises:
        HTTPException: 401 for invalid credentials, 403 for inactive account
    """
    print(f"🔐 Login attempt - Email: {credentials.email}")
    
    # Find admin by email
    admin = db.query(Admin).filter(Admin.email == credentials.email).first()
    
    if not admin:
        print(f"❌ Admin not found for email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_ERROR_INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is active
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AUTH_ERROR_INACTIVE_ACCOUNT,
        )
    
    # Update last login timestamp
    admin.last_login = get_wib_now()
    db.commit()
    
    return _create_login_response(admin)


@router.post("/register", response_model=AdminLoginResponse)
async def register(
    data: AdminRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register new admin (for development/setup only).
    In production, admins should be created via secure backend method.
    
    Args:
        data: Email, username, and password
        db: Database session
        
    Returns:
        AdminLoginResponse with access token
        
    Raises:
        HTTPException: 400 if email or username already exists
    """
    # Check if admin with email already exists
    existing_email = db.query(Admin).filter(Admin.email == data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=AUTH_ERROR_EMAIL_EXISTS
        )
    
    # Check if admin with username already exists
    existing_username = db.query(Admin).filter(Admin.username == data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=AUTH_ERROR_USERNAME_EXISTS
        )
    
    # Create new admin
    admin = Admin(
        email=data.email,
        username=data.username,
        password_hash=get_password_hash(data.password),
        is_active=1
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return _create_login_response(admin)
