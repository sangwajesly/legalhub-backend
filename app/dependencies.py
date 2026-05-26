"""
FastAPI dependency injection for authentication and services
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from typing import Optional

from app.utils.security import verify_access_token
import app.services.auth_service as auth_module
from app.models.user import User, UserRole

# Security scheme for JWT Bearer tokens
security = HTTPBearer()
# optional bearer that doesn't raise when missing
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> User:
    """
    Bypassed Authentication Dependency for Demo / Production Public Mode.
    Immediately returns a mock citizen user.
    """
    from datetime import datetime, UTC
    return User(
        uid="mock_citizen_demo_uid",
        email="demo@legalhub.com",
        display_name="Demo User",
        role="citizen",
        email_verified=True,
        phone_number="+237123456789",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure user is active (not disabled)

    Args:
        current_user: Current authenticated user

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive
    """
    # Add your inactive/disabled user logic here if needed
    # For now, we'll just return the user
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security_optional),
) -> Optional[User]:
    """
    Dependency to optionally get current user (doesn't raise error if not authenticated)

    Args:
        credentials: Optional HTTP Authorization credentials

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            return None

        user = await auth_module.auth_service.get_current_user(user_id)
        return user

    except (JWTError, HTTPException):
        return None


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific user role

    Args:
        required_role: The role required to access the endpoint

    Returns:
        Dependency function
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}",
            )
        return current_user

    return role_checker


def require_roles(*roles: UserRole):
    """
    Dependency factory to require one of multiple roles

    Args:
        roles: Tuple of acceptable roles

    Returns:
        Dependency function
    """

    async def roles_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            roles_str = ", ".join([role.value for role in roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {roles_str}",
            )
        return current_user

    return roles_checker


# Convenience dependencies for specific roles
async def require_lawyer(
    current_user: User = Depends(require_role(UserRole.LAWYER)),
) -> User:
    """Require user to be a lawyer"""
    return current_user


async def require_organization(
    current_user: User = Depends(require_role(UserRole.ORGANIZATION)),
) -> User:
    """Require user to be an organization"""
    return current_user


async def require_admin(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> User:
    """Require user to be an admin"""
    return current_user
