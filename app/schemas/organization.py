"""
Schemas for organization profiles and responses
"""

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime


class OrganizationProfile(BaseModel):
    uid: str = Field(..., description="Organization UID")
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    organization_type: Optional[str] = None
    contact_person: Optional[str] = None
    verified: bool = Field(default=False)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uid": "org_123",
                "display_name": "Legal Aid NGO",
                "email": "contact@legalaid.org",
                "location": "Yaounde",
                "website": "https://legalaid.org",
                "registration_number": "REG-2024-001",
                "organization_type": "NGO",
                "contact_person": "Jane Director",
                "verified": True,
            }
        }
    )


class OrganizationCreate(BaseModel):
    display_name: str
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    organization_type: Optional[str] = None
    contact_person: Optional[str] = None


class OrganizationUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    organization_type: Optional[str] = None
    contact_person: Optional[str] = None


class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationProfile]
    total: int
    page: int
    pageSize: int
