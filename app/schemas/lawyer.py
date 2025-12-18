"""
Schemas for lawyer profiles and responses
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class LawyerProfile(BaseModel):
    uid: str = Field(..., description="User UID")
    display_name: Optional[str] = Field(None, alias="displayName")
    email: Optional[str] = None
    profile_picture: Optional[str] = Field(None, alias="profilePicture")
    bio: Optional[str] = None
    location: Optional[str] = None
    license_number: Optional[str] = Field(None, alias="licenseNumber")
    jurisdictions: List[str] = Field(default_factory=list)
    practice_areas: List[str] = Field(
        default_factory=list, alias="practiceAreas")
    hourly_rate: Optional[float] = Field(None, alias="hourlyRate")
    years_experience: Optional[int] = Field(None, alias="yearsExperience")
    languages: List[str] = Field(default_factory=list)
    verified: bool = Field(default=False)
    rating: Optional[float] = None
    num_reviews: Optional[int] = Field(None, alias="numReviews")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uid": "lawyer_123",
                "display_name": "Jane Lawyer",
                "email": "jane.lawyer@example.com",
                "license_number": "BAR-12345",
                "practice_areas": ["employment", "family"],
                "hourly_rate": 75.0,
                "years_experience": 8,
                "languages": ["en", "fr"],
                "verified": True,
                "rating": 4.8,
                "num_reviews": 23,
            }
        }
    )


class LawyerCreate(BaseModel):
    display_name: str = Field(..., alias="displayName")
    email: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    license_number: Optional[str] = Field(None, alias="licenseNumber")
    practice_areas: List[str] = Field(
        default_factory=list, alias="practiceAreas")
    hourly_rate: Optional[float] = Field(None, alias="hourlyRate")

    model_config = ConfigDict(populate_by_name=True)


class LawyerUpdate(BaseModel):
    display_name: Optional[str] = Field(None, alias="displayName")
    bio: Optional[str] = None
    location: Optional[str] = None
    practice_areas: Optional[List[str]] = Field(None, alias="practiceAreas")
    hourly_rate: Optional[float] = Field(None, alias="hourlyRate")
    verified: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class LawyerListResponse(BaseModel):
    lawyers: List[LawyerProfile]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)
