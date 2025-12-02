"""
Schemas for lawyer profiles and responses
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class LawyerProfile(BaseModel):
    uid: str = Field(..., description="User UID")
    display_name: Optional[str] = None
    email: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    license_number: Optional[str] = None
    jurisdictions: List[str] = Field(default_factory=list)
    practice_areas: List[str] = Field(default_factory=list)
    hourly_rate: Optional[float] = None
    years_experience: Optional[int] = None
    languages: List[str] = Field(default_factory=list)
    verified: bool = Field(default=False)
    rating: Optional[float] = None
    num_reviews: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
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
                "num_reviews": 23
            }
        }
    )


class LawyerCreate(BaseModel):
    display_name: str
    email: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    license_number: Optional[str] = None
    practice_areas: List[str] = Field(default_factory=list)
    hourly_rate: Optional[float] = None


class LawyerUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    practice_areas: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    verified: Optional[bool] = None


class LawyerListResponse(BaseModel):
    lawyers: List[LawyerProfile]
    total: int
    page: int
    pageSize: int
