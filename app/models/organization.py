"""
Organization model and Firestore conversion helpers
"""

from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, EmailStr


def utc_now():
    return datetime.now(timezone.utc)


class Organization(BaseModel):
    uid: str
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
    verified: bool = False
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


def firestore_organization_to_model(doc: dict, uid: str) -> Organization:
    return Organization.model_validate({**doc, "uid": uid})


def organization_model_to_firestore(org: Organization) -> dict:
    data = org.model_dump(by_alias=True)
    data.pop("uid", None)
    return data
