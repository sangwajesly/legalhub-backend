"""
Authentication API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    AuthResponse,
    PasswordReset,
    AuthTokenRequest, # Added AuthTokenRequest
)
from app.services.auth_service import auth_service
from app.dependencies import get_current_user
from app.models.user import User

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(user_data: UserRegister): # Changed payload to user_data using UserRegister
    """
    Register a new user

    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, must include uppercase, lowercase, and digit)
    - **display_name**: User's display name
    - **role**: User role (user, lawyer, organization)
    - **phone_number**: Optional phone number

    Returns user data and authentication tokens
    """
    try:
        result = await auth_service.register_user(user_data)

        # Convert user to response format
        user_response = UserResponse(
            uid=result["user"].uid,
            email=result["user"].email,
            display_name=result["user"].display_name,
            role=result["user"].role,
            phone_number=result["user"].phone_number,
            profile_picture=result["user"].profile_picture,
            email_verified=result["user"].email_verified,
            created_at=result["user"].created_at,
            updated_at=result["user"].updated_at,
        )

        # Convert tokens to response format
        token_response = Token(**result["tokens"])

        # Return structured response for server-side registration
        return AuthResponse(user=user_response, tokens=token_response)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )

@router.post("/google", response_model=AuthResponse)
async def google_login(payload: dict):
    """
    Authenticate with Google using Firebase ID Token
    
    - **idToken**: valid Firebase ID token from client
    
    Returns user data and authentication tokens
    """
    try:
        id_token = payload.get("idToken")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="idToken is required"
            )
            
        result = await auth_service.authenticate_with_social_provider(id_token)
        
        # Convert user to response format
        user_response = UserResponse(
            uid=result["user"].uid,
            email=result["user"].email,
            display_name=result["user"].display_name,
            role=result["user"].role,
            phone_number=result["user"].phone_number,
            profile_picture=result["user"].profile_picture,
            email_verified=result["user"].email_verified,
            created_at=result["user"].created_at,
            updated_at=result["user"].updated_at,
        )
        
        # Convert tokens to response format
        token_response = Token(**result["tokens"])
        
        return AuthResponse(user=user_response, tokens=token_response)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google login failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: AuthTokenRequest): # Changed payload to request using AuthTokenRequest
    """
    Authenticate user with Firebase ID Token and receive internal tokens

    - **id_token**: Firebase ID token obtained from client-side authentication

    Returns user data and authentication tokens
    """
    try:
        # Call the updated login_user from auth_service
        result = await auth_service.login_user(request.id_token)

        # Convert user to response format
        user_response = UserResponse(
            uid=result["user"].uid,
            email=result["user"].email,
            display_name=result["user"].display_name,
            role=result["user"].role,
            phone_number=result["user"].phone_number,
            profile_picture=result["user"].profile_picture,
            email_verified=result["user"].email_verified,
            created_at=result["user"].created_at,
            updated_at=result["user"].updated_at,
        )

        # Convert tokens to response format
        token_response = Token(**result["tokens"])

        return AuthResponse(user=user_response, tokens=token_response)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Requires authentication.
    """
    return UserResponse(
        uid=current_user.uid,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        phone_number=current_user.phone_number,
        profile_picture=current_user.profile_picture,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
