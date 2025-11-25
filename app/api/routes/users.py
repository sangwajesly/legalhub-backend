"""
User profile management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from app.schemas.auth import UserResponse, UserUpdate
from app.services.firebase_service import firebase_service
from app.dependencies import get_current_user
from app.models.user import User

# Create router
router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile
    
    Requires authentication.
    Returns complete user profile information.
    """
    return UserResponse(
        uid=current_user.uid,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role.value,
        phone_number=current_user.phone_number,
        profile_picture=current_user.profile_picture,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get("/profile/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str):
    """
    Get user profile by ID
    
    - **user_id**: User's unique identifier
    
    Returns public user profile information.
    """
    try:
        user = await firebase_service.get_user_by_uid(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            uid=user.uid,
            email=user.email,
            display_name=user.display_name,
            role=user.role.value,
            phone_number=user.phone_number,
            profile_picture=user.profile_picture,
            email_verified=user.email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile
    
    - **display_name**: New display name (optional)
    - **phone_number**: New phone number (optional)
    - **profile_picture**: URL to profile picture (optional)
    - **bio**: User biography (optional)
    - **location**: User location (optional)
    
    Requires authentication.
    """
    try:
        # Prepare update data (only include non-None values)
        update_data = {}
        
        if profile_data.display_name is not None:
            update_data["displayName"] = profile_data.display_name
        
        if profile_data.phone_number is not None:
            update_data["phoneNumber"] = profile_data.phone_number
        
        if profile_data.profile_picture is not None:
            update_data["profilePicture"] = profile_data.profile_picture
        
        # Update main user data
        if update_data:
            updated_user = await firebase_service.update_user(current_user.uid, update_data)
        else:
            updated_user = current_user
        
        # Update extended profile (bio, location)
        profile_update = {}
        if profile_data.bio is not None:
            profile_update["bio"] = profile_data.bio
        
        if profile_data.location is not None:
            profile_update["location"] = profile_data.location
        
        if profile_update:
            await firebase_service.update_user_profile(current_user.uid, profile_update)
        
        return UserResponse(
            uid=updated_user.uid,
            email=updated_user.email,
            display_name=updated_user.display_name,
            role=updated_user.role.value,
            phone_number=updated_user.phone_number,
            profile_picture=updated_user.profile_picture,
            email_verified=updated_user.email_verified,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.delete("/profile")
async def delete_user_account(current_user: User = Depends(get_current_user)):
    """
    Delete current user's account
    
    Requires authentication.
    This action is irreversible and will delete all user data.
    """
    try:
        success = await firebase_service.delete_user(current_user.uid)
        
        if success:
            return {"message": "Account deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}"
        )


@router.get("/profile/{user_id}/extended")
async def get_extended_profile(user_id: str):
    """
    Get extended user profile including bio, location, preferences
    
    - **user_id**: User's unique identifier
    
    Returns extended profile information if available.
    """
    try:
        # Get basic user info
        user = await firebase_service.get_user_by_uid(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get extended profile
        profile = await firebase_service.get_user_profile(user_id)
        
        response = {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role.value,
            "phone_number": user.phone_number,
            "profile_picture": user.profile_picture,
            "email_verified": user.email_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        # Add extended profile data if available
        if profile:
            response.update({
                "bio": profile.bio,
                "location": profile.location,
                "preferences": profile.preferences,
                "notification_settings": profile.notification_settings
            })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving profile: {str(e)}"
        )