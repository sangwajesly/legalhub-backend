"""
Authentication API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

# authentication schemas

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    AuthResponse,
    PasswordReset,
    AuthTokenRequest,
    VerifyTokenRequest,
    FullUserProfileResponse  # Added FullUserProfileResponse
)
from app.services.auth_service import auth_service
from app.dependencies import get_current_user
from app.models.user import User, UserProfile # Also import UserProfile

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", deprecated=True, status_code=status.HTTP_410_GONE)
async def register(user_data: UserRegister):
    """
    **DEPRECATED**: Registration is now handled by frontend via Firebase SDK.

    Frontend should:
    1. Use Firebase Authentication SDK for email/password registration
    2. Get Firebase ID token after registration
    3. Send token to `/api/v1/auth/verify-token` to sync user with backend

    This endpoint will be removed in a future version.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Registration is now handled by frontend. Use Firebase SDK for registration."
    )


@router.post("/verify-token", response_model=AuthResponse)
async def verify_token(payload: VerifyTokenRequest):
    """
    Verify Firebase ID Token and sync/create user in backend (BYPASSED)
    """
    from datetime import datetime, UTC
    user_response = UserResponse(
        uid="mock_citizen_demo_uid",
        email="demo@legalhub.com",
        displayName="Demo User",
        role="citizen",
        phoneNumber="+237123456789",
        profilePicture=None,
        emailVerified=True,
        createdAt=datetime.now(UTC),
        updatedAt=datetime.now(UTC)
    )
    token_response = Token(
        access_token="mock_access_token_demo",
        refresh_token="mock_refresh_token_demo",
        token_type="bearer",
        expires_in=3600
    )
    return AuthResponse(user=user_response, tokens=token_response)


# Keep /google as an alias for backward compatibility (deprecated)
@router.post("/google", deprecated=True, response_model=AuthResponse)
async def google_login(payload: dict):
    """
    **DEPRECATED**: Use `/api/v1/auth/verify-token` instead.

    This endpoint is kept for backward compatibility only.
    """
    return await verify_token(payload)


@router.post("/login", deprecated=True, status_code=status.HTTP_410_GONE)
async def login(payload: UserLogin | AuthTokenRequest):
    """
    **DEPRECATED**: Email/password login is now handled by frontend via Firebase SDK.

    Frontend should:
    1. Use Firebase Authentication SDK for email/password login
    2. Get Firebase ID token after authentication
    3. Send token to `/api/v1/auth/verify-token` to sync user with backend

    This endpoint will be removed in a future version.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Email/password login is now handled by frontend. Use Firebase SDK for login."
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token

    Returns new access and refresh tokens
    """
    try:
        tokens = await auth_service.refresh_access_token(token_data.refresh_token)
        return Token(**tokens)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user

    Requires authentication. Client should discard tokens after this call.
    """
    try:
        await auth_service.logout_user(current_user.uid)
        return {"message": "Successfully logged out"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}",
        )


@router.post("/password-reset")
async def request_password_reset(reset_data: PasswordReset):
    """
    Request password reset email

    - **email**: Email address to send reset link to

    Always returns success (to prevent email enumeration)
    """
    try:
        await auth_service.send_password_reset_email(reset_data.email)
        return {"message": "If the email exists, a password reset link has been sent"}

    except Exception:
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/verify-email/{user_id}")
async def verify_email(user_id: str):
    """
    Verify user's email address

    - **user_id**: User's unique identifier

    This would typically be called from an email verification link
    """
    try:
        success = await auth_service.verify_email(user_id)
        if success:
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification failed",
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )


@router.get("/me", response_model=FullUserProfileResponse)  # Changed response_model
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Requires authentication. Returns a combined User and UserProfile object.
    """
    try:
        user_profile = await auth_service.firebase.get_user_profile(current_user.uid)

        # Combine User and UserProfile data
        user_data = current_user.model_dump(by_alias=True)
        if user_profile:
            profile_data = user_profile.model_dump(by_alias=True)
            # Merge, with profile_data overriding common fields if necessary
            combined_data = {**user_data, **profile_data}
        else:
            combined_data = user_data

        return FullUserProfileResponse(**combined_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}",
        )
