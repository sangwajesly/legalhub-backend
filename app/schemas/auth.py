"""
Authentication request/response schemas
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, UserProfile


class UserRegister(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )
    display_name: str = Field(..., min_length=2,
                              max_length=100, alias="displayName")
    role: str = "citizen"
    phone_number: Optional[str] = Field(None, alias="phoneNumber")

    # Optional Lawyer Fields
    bio: Optional[str] = None
    location: Optional[str] = None
    license_number: Optional[str] = Field(None, alias="licenseNumber")
    practice_areas: Optional[list[str]] = Field(default=None, alias="practiceAreas")
    hourly_rate: Optional[float] = Field(default=None, alias="hourlyRate")
    years_experience: Optional[int] = Field(default=None, alias="yearsExperience")

    @field_validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "display_name": "John Doe",
                "role": "citizen",
                "phone_number": "+237123456789",
            }
        }
    )


class AuthTokenRequest(BaseModel):
    """Schema for requests containing a Firebase ID token."""
    id_token: str = Field(
        ...,
        alias="idToken",
        description="Firebase ID token from client-side authentication."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "idToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
            }
        }
    )


class VerifyTokenRequest(AuthTokenRequest):
    """Schema for requests to /verify-token, including optional metadata."""
    name: Optional[str] = Field(None, description="Optional display name for new user registration.")
    role: Optional[UserRole] = Field(None, description="Optional role for new user registration.")
    
    # Optional Lawyer Fields for registration
    bio: Optional[str] = None
    location: Optional[str] = None
    license_number: Optional[str] = Field(None, alias="licenseNumber")
    practice_areas: Optional[list[str]] = Field(default=None, alias="practiceAreas")
    hourly_rate: Optional[float] = Field(default=None, alias="hourlyRate")
    years_experience: Optional[int] = Field(default=None, alias="yearsExperience")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "idToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
                "name": "New User",
                "role": "citizen"
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "SecurePass123"}
        }
    )


class Token(BaseModel):
    """Schema for authentication tokens"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""

    refresh_token: str


class PublicUserResponse(BaseModel):
    """Schema for public user profile (safe for viewing by others)"""
    uid: str
    display_name: Optional[str] = Field(None, alias="displayName")
    role: str
    profile_picture: Optional[str] = Field(None, alias="profilePicture")
    created_at: datetime = Field(..., alias="createdAt")
    # Exclude email, phone_number, updated_at, email_verified

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uid": "abc123xyz",
                "display_name": "John Doe",
                "role": "citizen",
                "profile_picture": "https://example.com/photo.jpg",
                "created_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user data response"""

    uid: str
    email: str
    display_name: Optional[str] = Field(None, alias="displayName")
    role: str
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    profile_picture: Optional[str] = Field(None, alias="profilePicture")
    email_verified: bool = Field(..., alias="emailVerified")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uid": "abc123xyz",
                "email": "user@example.com",
                "display_name": "John Doe",
                "role": "citizen",
                "phone_number": "+237123456789",
                "profile_picture": "https://example.com/photo.jpg",
                "email_verified": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class FullUserProfileResponse(UserResponse, UserProfile):
    """
    Combines User and UserProfile schemas for a complete user profile response.
    Note: Fields from UserProfile will override User fields if they have the same name.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uid": "abc123xyz",
                "email": "user@example.com",
                "display_name": "John Doe",
                "role": "citizen",
                "phone_number": "+237123456789",
                "profile_picture": "https://example.com/photo.jpg",
                "email_verified": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "bio": "Legal enthusiast seeking justice",
                "location": "Bamenda, Cameroon",
                "country": "Cameroon",
                "language_preference": "en",
                "timezone": "UTC",
                "email_notifications": True,
                "push_notifications": True,
                "sms_notifications": False,
                "profile_visibility": "public",
                "show_email": False,
                "interests": ["human rights", "environmental law"],
                "preferred_contact_method": "email",
                "fcm_token": "some_fcm_token_string",
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile"""

    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = None
    language_preference: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "John Updated",
                "phone_number": "+237987654321",
                "bio": "Legal enthusiast seeking justice",
                "location": "Bamenda, Cameroon",
            }
        }
    )


class PasswordReset(BaseModel):
    """Schema for password reset request"""

    email: EmailStr

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "user@example.com"}}
    )


class PasswordChange(BaseModel):
    """Schema for password change"""

    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        return v


class AuthResponse(BaseModel):
    """Complete authentication response with user data and tokens"""

    user: UserResponse
    tokens: Token

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "uid": "abc123xyz",
                    "email": "user@example.com",
                    "display_name": "John Doe",
                    "role": "citizen",
                    "phone_number": "+237123456789",
                    "profile_picture": None,
                    "email_verified": True,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                },
                "tokens": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "token_type": "bearer",
                    "expires_in": 1800,
                },
            }
        }
    )
