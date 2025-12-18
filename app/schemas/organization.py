"""
Schemas for organization profiles and responses
"""

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime


class OrganizationProfile(BaseModel):
    uid: str = Field(..., description="Organization UID")
    display_name: Optional[str] = Field(None, alias="displayName")
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = Field(None, alias="profilePicture")
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = Field(
        None, alias="registrationNumber")
    organization_type: Optional[str] = Field(None, alias="organizationType")
    contact_person: Optional[str] = Field(None, alias="contactPerson")
    verified: bool = Field(default=False)
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
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
    display_name: str = Field(..., alias="displayName")
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = Field(
        None, alias="registrationNumber")
    organization_type: Optional[str] = Field(None, alias="organizationType")
    contact_person: Optional[str] = Field(None, alias="contactPerson")

    model_config = ConfigDict(populate_by_name=True)


class OrganizationUpdate(BaseModel):
    display_name: Optional[str] = Field(None, alias="displayName")
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = Field(
        None, alias="registrationNumber")
    organization_type: Optional[str] = Field(None, alias="organizationType")
    contact_person: Optional[str] = Field(None, alias="contactPerson")

    model_config = ConfigDict(populate_by_name=True)


class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationProfile]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)
