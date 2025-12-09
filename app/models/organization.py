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
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    organization_type: Optional[str] = None
    contact_person: Optional[str] = None
    verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict()


def firestore_organization_to_model(doc: dict, uid: str) -> Organization:
    return Organization(
        uid=uid,
        display_name=doc.get("displayName") or doc.get("display_name"),
        email=doc.get("email"),
        profile_picture=doc.get("profilePicture") or doc.get("profile_picture"),
        bio=doc.get("bio"),
        location=doc.get("location"),
        website=doc.get("website"),
        registration_number=doc.get("registrationNumber") or doc.get("registration_number"),
        organization_type=doc.get("organizationType") or doc.get("organization_type"),
        contact_person=doc.get("contactPerson") or doc.get("contact_person"),
        verified=doc.get("verified", False),
        created_at=doc.get("createdAt") or doc.get("created_at"),
        updated_at=doc.get("updatedAt") or doc.get("updated_at"),
    )


def organization_model_to_firestore(org: Organization) -> dict:
    return {
        "displayName": org.display_name,
        "email": org.email,
        "profilePicture": org.profile_picture,
        "bio": org.bio,
        "location": org.location,
        "website": org.website,
        "registrationNumber": org.registration_number,
        "organizationType": org.organization_type,
        "contactPerson": org.contact_person,
        "verified": org.verified,
        "createdAt": org.created_at,
        "updatedAt": org.updated_at,
    }
