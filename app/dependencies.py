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
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        Current user as a User Pydantic model

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract the token from the "Bearer <token>" scheme
    token = credentials.credentials
    if not token:
        raise credentials_exception

    try:
        # 1. Try Firebase ID token verification first
        decoded_token = auth_module.verify_id_token(token)
        if decoded_token:
            firebase_uid = decoded_token.get("uid")
            if firebase_uid:
                user = await auth_module.auth_service.get_current_user(firebase_uid)
                if user is None:
                    print(f"DEBUG: Firebase authenticated user {firebase_uid} not found in Firestore.")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Firebase authenticated user not found.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return user
            else:
                print("DEBUG: Firebase ID token decoded but missing UID.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Firebase ID token (missing UID).",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    except ValueError as e:
        print(f"DEBUG: Firebase ID token verification failed: {e}. Trying internal token next.")
        # Continue to try internal token if Firebase verification fails specifically with ValueError
        # from auth_module.verify_id_token (which re-raises specific Firebase Admin SDK errors)
    except Exception as e:
        # Catch any other unexpected errors during Firebase verification
        print(f"DEBUG: Unexpected error during Firebase ID token verification: {e}. Trying internal token next.")

    # 2. If Firebase ID token verification failed, try internal token
    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")

        if user_id:
            user = await auth_module.auth_service.get_current_user(user_id)
            if user is None:
                print(f"DEBUG: Internal token valid but user {user_id} not found in Firestore.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authenticated user not found.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
        else:
            print("DEBUG: Internal token valid but missing sub (user ID).")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid internal token (missing user ID).",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as e:
        print(f"DEBUG: Internal token verification failed: {e}.")
        # Fall through to final exception if both fail

    # If neither verification method succeeded
    raise credentials_exception


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
