"""
User Models for LegalHub Backend

This module defines the User and UserProfile models that represent
user data stored in Firebase Firestore.
"""

from datetime import datetime, timezone
from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Helper function for timezone-aware UTC datetime
def utc_now():
    """Get current UTC datetime (timezone-aware)"""
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    """User role enumeration"""

    USER = "user"
    LAWYER = "lawyer"
    ORGANIZATION = "organization"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model with common fields"""

    email: EmailStr
    display_name: str = Field(
        ..., min_length=2, max_length=100, description="User's display name"
    )
    role: Literal["user", "lawyer", "organization"] = Field(
        default="user", description="User role in the system"
    )
    profile_picture: Optional[str] = Field(
        default=None, description="URL to profile picture"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "role": "user",
                "profile_picture": "https://example.com/photos/user.jpg",
            }
        }
    )


class User(UserBase):
    """
    Complete User model representing a user in Firestore

    Collection: users/
    Document ID: uid (Firebase Auth UID)
    """

    uid: str = Field(..., description="Firebase Authentication UID")
    email_verified: bool = Field(default=False, description="Whether email is verified")
    phone_number: Optional[str] = Field(default=None, description="User's phone number")
    is_active: bool = Field(default=True, description="Whether account is active")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    created_at: Optional[datetime] = Field(
        default_factory=utc_now, description="Account creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=utc_now, description="Last update timestamp"
    )
    last_login: Optional[datetime] = Field(
        default=None, description="Last login timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uid": "firebase_user_uid_123",
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "role": "user",
                "email_verified": True,
                "phone_number": "+237123456789",
                "profile_picture": "https://example.com/photos/user.jpg",
                "is_active": True,
                "is_deleted": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-15T10:30:00",
            }
        }
    )


class UserProfile(BaseModel):
    """
    Extended user profile with additional information

    This can be stored as a subcollection or embedded in the user document
    Collection: users/{uid}/profile or embedded in users/{uid}
    """

    uid: str = Field(..., description="Reference to user UID")
    bio: Optional[str] = Field(
        default=None, max_length=500, description="User biography"
    )
    location: Optional[str] = Field(default=None, description="User's location/city")
    country: Optional[str] = Field(default=None, description="User's country")
    language_preference: str = Field(
        default="en", description="Preferred language code"
    )
    timezone: str = Field(default="UTC", description="User's timezone")

    # Notification preferences
    email_notifications: bool = Field(
        default=True, description="Receive email notifications"
    )
    push_notifications: bool = Field(
        default=True, description="Receive push notifications"
    )
    sms_notifications: bool = Field(
        default=False, description="Receive SMS notifications"
    )

    # Privacy settings
    profile_visibility: Literal["public", "private", "connections"] = Field(
        default="public", description="Who can view the profile"
    )
    show_email: bool = Field(default=False, description="Show email on public profile")

    # Additional metadata
    interests: list[str] = Field(
        default_factory=list, description="Legal topics of interest"
    )
    preferred_contact_method: Optional[Literal["email", "phone", "chat"]] = Field(
        default="email", description="Preferred method of contact"
    )

    # FCM token for push notifications
    fcm_token: Optional[str] = Field(
        default=None, description="Firebase Cloud Messaging token"
    )

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uid": "firebase_user_uid_123",
                "bio": "Legal enthusiast interested in human rights law",
                "location": "Bamenda",
                "country": "Cameroon",
                "language_preference": "en",
                "timezone": "Africa/Douala",
                "email_notifications": True,
                "push_notifications": True,
                "sms_notifications": False,
                "profile_visibility": "public",
                "show_email": False,
                "interests": ["human rights", "criminal law", "civil rights"],
                "preferred_contact_method": "email",
                "fcm_token": "fcm_token_string_here",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        }
    )


class UserInDB(User):
    """
    User model as stored in database (includes sensitive fields)
    This extends User with fields that should not be exposed in API responses
    """

    password_hash: Optional[str] = Field(
        default=None, description="Hashed password (for email/password auth)"
    )
    refresh_token: Optional[str] = Field(
        default=None, description="Current refresh token"
    )
    password_reset_token: Optional[str] = Field(
        default=None, description="Password reset token"
    )
    password_reset_expires: Optional[datetime] = Field(
        default=None, description="Reset token expiration"
    )
    failed_login_attempts: int = Field(
        default=0, description="Count of failed login attempts"
    )
    account_locked_until: Optional[datetime] = Field(
        default=None, description="Account lock expiration"
    )


class UserStats(BaseModel):
    """
    User statistics and engagement metrics
    Can be stored as subcollection or calculated on-demand
    """

    uid: str
    total_chats: int = Field(default=0, description="Total chat sessions")
    total_cases_reported: int = Field(default=0, description="Total cases reported")
    total_bookings: int = Field(default=0, description="Total lawyer bookings")
    total_articles_read: int = Field(default=0, description="Articles read count")
    total_articles_written: int = Field(
        default=0, description="Articles written (for lawyers)"
    )
    total_reviews_given: int = Field(default=0, description="Reviews given to lawyers")
    reputation_score: float = Field(default=0.0, description="User reputation score")
    last_activity: Optional[datetime] = Field(
        default=None, description="Last activity timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uid": "firebase_user_uid_123",
                "total_chats": 15,
                "total_cases_reported": 2,
                "total_bookings": 3,
                "total_articles_read": 45,
                "total_articles_written": 0,
                "total_reviews_given": 2,
                "reputation_score": 85.5,
                "last_activity": "2024-01-15T14:30:00",
            }
        }
    )


# Helper function to convert Firestore document to User model
def firestore_user_to_model(doc_data: dict, uid: str) -> User:
    """
    Convert Firestore document data to User model

    Args:
        doc_data: Dictionary from Firestore document
        uid: User's Firebase UID

    Returns:
        User model instance
    """
    return User(
        uid=uid,
        email=doc_data.get("email"),
        display_name=doc_data.get("displayName", doc_data.get("display_name")),
        role=doc_data.get("role", "user"),
        email_verified=doc_data.get(
            "emailVerified", doc_data.get("email_verified", False)
        ),
        phone_number=doc_data.get("phoneNumber", doc_data.get("phone_number")),
        profile_picture=doc_data.get("photoURL", doc_data.get("photo_url")),
        is_active=doc_data.get("isActive", doc_data.get("is_active", True)),
        is_deleted=doc_data.get("isDeleted", doc_data.get("is_deleted", False)),
        created_at=doc_data.get("createdAt", doc_data.get("created_at")),
        updated_at=doc_data.get("updatedAt", doc_data.get("updated_at")),
        last_login=doc_data.get("lastLogin", doc_data.get("last_login")),
    )


# Helper function to convert User model to Firestore document
def user_model_to_firestore(user: User) -> dict:
    """
    Convert User model to Firestore document format

    Args:
        user: User model instance

    Returns:
        Dictionary for Firestore storage
    """
    return {
        "email": user.email,
        "displayName": user.display_name,
        "role": user.role,
        "emailVerified": user.email_verified,
        "phoneNumber": user.phone_number,
        "profilePicture": user.profile_picture,
        "isActive": user.is_active,
        "isDeleted": user.is_deleted,
        "createdAt": user.created_at,
        "updatedAt": user.updated_at,
        "lastLogin": user.last_login,
    }
