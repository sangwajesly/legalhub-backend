"""
Security utilities for password hashing and JWT token management
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from app.config import settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": datetime.now(UTC), "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Data to encode in the token

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.now(UTC), "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify an access token

    Args:
        token: Access token to verify

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or not an access token
    """
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise JWTError("Invalid token type")

    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    Verify a refresh token

    Args:
        token: Refresh token to verify

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or not a refresh token
    """
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")

    return payload


def create_token_pair(user_id: str, email: str, role: str) -> Dict[str, Any]:
    """
    Create both access and refresh tokens for a user

    Args:
        user_id: User's unique identifier
        email: User's email
        role: User's role

    Returns:
        Dictionary containing access_token, refresh_token, and expiration info
    """
    token_data = {"sub": user_id, "email": email, "role": role}

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    }
