"""
Authentication Schemas for Request/Response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AdminLoginRequest(BaseModel):
    """Admin login request"""
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response"""
    access_token: str
    token_type: str = "bearer"
    email: str
    username: str


class AdminRegisterRequest(BaseModel):
    """Admin registration request"""
    email: EmailStr
    username: str
    password: str


class AdminResponse(BaseModel):
    """Admin user response"""
    id: int
    email: str
    username: str
    is_active: int
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    role: Optional[str] = None
