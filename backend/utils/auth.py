"""
Authentication Utilities - Password Hashing and Verification

Provides secure password hashing and verification using PBKDF2-HMAC-SHA256.
All passwords are salted with cryptographically secure random values.
"""
import hashlib
import secrets
from typing import Tuple

# Password hashing constants
PASSWORD_HASH_ALGORITHM = 'sha256'
PASSWORD_HASH_ITERATIONS = 100000
SALT_LENGTH = 32  # 64 character hex string
SALT_DELIMITER = '$'


def _generate_salt() -> str:
    """
    Generate cryptographically secure random salt.
    
    Returns:
        64-character hexadecimal salt string
    """
    return secrets.token_hex(SALT_LENGTH)


def _compute_password_hash(password: str, salt: str) -> str:
    """
    Compute PBKDF2-HMAC-SHA256 hash of password with salt.
    
    Args:
        password: Plain text password
        salt: Hexadecimal salt string
        
    Returns:
        Hexadecimal hash string
    """
    pwd_hash = hashlib.pbkdf2_hmac(
        PASSWORD_HASH_ALGORITHM,
        password.encode(),
        salt.encode(),
        PASSWORD_HASH_ITERATIONS
    )
    return pwd_hash.hex()


def _extract_salt_and_hash(password_hash: str) -> Tuple[str, str]:
    """
    Extract salt and hash from combined string.
    
    Args:
        password_hash: Combined salt and hash string (salt$hash format)
        
    Returns:
        Tuple of (salt, hash)
        
    Raises:
        ValueError: If format is invalid
    """
    parts = password_hash.split(SALT_DELIMITER)
    if len(parts) != 2:
        raise ValueError("Invalid password hash format")
    return parts[0], parts[1]


def hash_password(password: str) -> str:
    """
    Hash a plain text password with salt for secure storage.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password in format: salt$hash
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> len(hashed) > 100  # Should be long hash string
        True
    """
    salt = _generate_salt()
    pwd_hash = _compute_password_hash(password, salt)
    return f"{salt}{SALT_DELIMITER}{pwd_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain text password against a stored hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored hashed password (salt$hash format)
        
    Returns:
        True if password matches, False otherwise
        
    Note:
        Always returns False on format errors rather than raising exceptions
        to prevent timing attacks and information leakage.
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    try:
        salt, stored_hash = _extract_salt_and_hash(password_hash)
        computed_hash = _compute_password_hash(password, salt)
        return computed_hash == stored_hash
    except (ValueError, AttributeError):
        # Invalid format or None value - return False silently
        return False

