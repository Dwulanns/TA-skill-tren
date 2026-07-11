"""
Authentication Configuration and JWT Setup

Handles JWT token creation, validation, password hashing, and timezone management.
All configuration values should be set via environment variables.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import os
from dotenv import load_dotenv

from constants import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
BCRYPT_ROUNDS = 12

# ============================================================================
# TIMEZONE UTILITIES
# ============================================================================

# Timezone: WIB (Western Indonesian Time) = UTC+7
WIB_OFFSET = timezone(timedelta(hours=7))


def get_wib_now() -> datetime:
    """
    Get current datetime in WIB (Western Indonesian Time) timezone.
    
    Returns:
        Current datetime in WIB without timezone info
        
    Example:
        >>> now = get_wib_now()
        >>> isinstance(now, datetime)
        True
    """
    return datetime.now(WIB_OFFSET).replace(tzinfo=None)


# ============================================================================
# PASSWORD HASHING
# ============================================================================

def _encode_password_if_string(password: str) -> bytes:
    """
    Encode password to bytes if it's a string.
    
    Args:
        password: Password string
        
    Returns:
        Password as bytes
    """
    return password.encode('utf-8') if isinstance(password, str) else password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password from database
        
    Returns:
        True if password matches, False otherwise
        
    Note:
        Returns False on any error instead of raising exceptions
        to prevent information leakage.
        
    Example:
        >>> hashed = get_password_hash("mypassword")
        >>> verify_password("mypassword", hashed)
        True
    """
    try:
        plain_bytes = _encode_password_if_string(plain_password)
        hashed_bytes = _encode_password_if_string(hashed_password)
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hashed password as string
        
    Example:
        >>> hashed = get_password_hash("mypassword")
        >>> len(hashed) > 50
        True
    """
    password_bytes = _encode_password_if_string(password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with expiration.
    
    Args:
        data: Payload data to encode in token (typically {"sub": user_id})
        expires_delta: Optional custom expiration delta (default from config)
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> len(token) > 100
        True
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = get_wib_now() + expires_delta
    else:
        expire = get_wib_now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload as dict, or None if invalid/expired
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user@example.com'
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

