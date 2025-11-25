"""
LegalHub Backend Application Package
"""
__version__ = "1.0.0"
__app_name__ = "LegalHub Backend"

# app/__init__.py
# This file makes the app directory a Python package

# app/models/__init__.py
"""
Data models for LegalHub
"""
from app.models.user import User, UserProfile, UserRole

__all__ = ["User", "UserProfile", "UserRole"]


# app/schemas/__init__.py
"""
Pydantic schemas for request/response validation
"""
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    UserUpdate,
    PasswordReset,
    PasswordChange,
    AuthResponse
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenRefresh",
    "UserResponse",
    "UserUpdate",
    "PasswordReset",
    "PasswordChange",
    "AuthResponse"
]


# app/services/__init__.py
"""
Business logic services
"""
from app.services.firebase_service import firebase_service
from app.services.auth_service import auth_service

__all__ = ["firebase_service", "auth_service"]


# app/utils/__init__.py
"""
Utility functions and helpers
"""
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    verify_access_token,
    verify_refresh_token
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "verify_access_token",
    "verify_refresh_token"
]


# app/api/__init__.py
"""
API routes and endpoints
"""

# app/api/routes/__init__.py
"""
API route modules
"""
from app.api.routes import auth, users

__all__ = ["auth", "users"]