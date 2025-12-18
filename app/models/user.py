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
        ..., min_length=2, max_length=100, description="User's display name", alias="displayName"
    )
    role: Literal["user", "lawyer", "organization"] = Field(
        default="user", description="User role in the system"
    )
    profile_picture: Optional[str] = Field(
        default=None, description="URL to profile picture", alias="profilePicture"
    )
    model_config = ConfigDict(
        populate_by_name=True,
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
    email_verified: bool = Field(
        default=False, description="Whether email is verified", alias="emailVerified")
    phone_number: Optional[str] = Field(
        default=None, description="User's phone number", alias="phoneNumber")
    is_active: bool = Field(
        default=True, description="Whether account is active", alias="isActive")
    is_deleted: bool = Field(
        default=False, description="Soft delete flag", alias="isDeleted")
    created_at: Optional[datetime] = Field(
        default_factory=utc_now, description="Account creation timestamp", alias="createdAt"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=utc_now, description="Last update timestamp", alias="updatedAt"
    )
    last_login: Optional[datetime] = Field(
        default=None, description="Last login timestamp", alias="lastLogin"
    )

    model_config = ConfigDict(
        populate_by_name=True,
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
    location: Optional[str] = Field(
        default=None, description="User's location/city")
    country: Optional[str] = Field(default=None, description="User's country")
    language_preference: str = Field(
        default="en", description="Preferred language code", alias="languagePreference"
    )
    timezone: str = Field(default="UTC", description="User's timezone")

    # Notification preferences
    email_notifications: bool = Field(
        default=True, description="Receive email notifications", alias="emailNotifications"
    )
    push_notifications: bool = Field(
        default=True, description="Receive push notifications", alias="pushNotifications"
    )
    sms_notifications: bool = Field(
        default=False, description="Receive SMS notifications", alias="smsNotifications"
    )

    # Privacy settings
    profile_visibility: Literal["public", "private", "connections"] = Field(
        default="public", description="Who can view the profile", alias="profileVisibility"
    )
    show_email: bool = Field(
        default=False, description="Show email on public profile", alias="showEmail")

    # Additional metadata
    interests: list[str] = Field(
        default_factory=list, description="Legal topics of interest"
    )
    preferred_contact_method: Optional[Literal["email", "phone", "chat"]] = Field(
        default="email", description="Preferred method of contact", alias="preferredContactMethod"
    )

    # FCM token for push notifications
    fcm_token: Optional[str] = Field(
        default=None, description="Firebase Cloud Messaging token", alias="fcmToken"
    )

    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")
    updated_at: datetime = Field(default_factory=utc_now, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
    )


class UserInDB(User):
    """
    User model as stored in database (includes sensitive fields)
    This extends User with fields that should not be exposed in API responses
    """

    password_hash: Optional[str] = Field(
        default=None, description="Hashed password (for email/password auth)", alias="passwordHash"
    )
    refresh_token: Optional[str] = Field(
        default=None, description="Current refresh token", alias="refreshToken"
    )
    password_reset_token: Optional[str] = Field(
        default=None, description="Password reset token", alias="passwordResetToken"
    )
    password_reset_expires: Optional[datetime] = Field(
        default=None, description="Reset token expiration", alias="passwordResetExpires"
    )
    failed_login_attempts: int = Field(
        default=0, description="Count of failed login attempts", alias="failedLoginAttempts"
    )
    account_locked_until: Optional[datetime] = Field(
        default=None, description="Account lock expiration", alias="accountLockedUntil"
    )


class UserStats(BaseModel):
    """
    User statistics and engagement metrics
    Can be stored as subcollection or calculated on-demand
    """

    uid: str
    total_chats: int = Field(
        default=0, description="Total chat sessions", alias="totalChats")
    total_cases_reported: int = Field(
        default=0, description="Total cases reported", alias="totalCasesReported")
    total_bookings: int = Field(
        default=0, description="Total lawyer bookings", alias="totalBookings")
    total_articles_read: int = Field(
        default=0, description="Articles read count", alias="totalArticlesRead")
    total_articles_written: int = Field(
        default=0, description="Articles written (for lawyers)", alias="totalArticlesWritten"
    )
    total_reviews_given: int = Field(
        default=0, description="Reviews given to lawyers", alias="totalReviewsGiven")
    reputation_score: float = Field(
        default=0.0, description="User reputation score", alias="reputationScore")
    last_activity: Optional[datetime] = Field(
        default=None, description="Last activity timestamp", alias="lastActivity"
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


# Helper function to convert Firestore document to User model
def firestore_user_to_model(doc_data: dict, uid: str) -> User:
    return User.model_validate({**doc_data, "uid": uid})


# Helper function to convert User model to Firestore document
def user_model_to_firestore(user: User) -> dict:
    # Use by_alias=True to get camelCase for Firestore
    data = user.model_dump(by_alias=True)
    # Exclude uid as it's typically the document ID
    data.pop("uid", None)
    return data
