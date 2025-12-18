"""
Lawyer model and Firestore conversion helpers
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now():
    return datetime.now(timezone.utc)


class Lawyer(BaseModel):
    uid: str
    display_name: Optional[str] = Field(None, alias="displayName")
    email: Optional[str] = None
    profile_picture: Optional[str] = Field(None, alias="profilePicture")
    bio: Optional[str] = None
    location: Optional[str] = None
    license_number: Optional[str] = Field(None, alias="licenseNumber")
    jurisdictions: list[str] = Field(default_factory=list)
    practice_areas: list[str] = Field(
        default_factory=list, alias="practiceAreas")
    hourly_rate: Optional[float] = Field(None, alias="hourlyRate")
    years_experience: Optional[int] = Field(None, alias="yearsExperience")
    languages: list[str] = Field(default_factory=list)
    verified: bool = False
    rating: Optional[float] = None
    num_reviews: Optional[int] = Field(None, alias="numReviews")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


def firestore_lawyer_to_model(doc: dict, uid: str) -> Lawyer:
    return Lawyer(
        uid=uid,
        display_name=doc.get("displayName") or doc.get("display_name"),
        email=doc.get("email"),
        profile_picture=doc.get(
            "profilePicture") or doc.get("profile_picture"),
        bio=doc.get("bio"),
        location=doc.get("location"),
        license_number=doc.get("licenseNumber") or doc.get("license_number"),
        jurisdictions=doc.get("jurisdictions", []),
        practice_areas=doc.get("practiceAreas", []),
        hourly_rate=doc.get("hourlyRate") or doc.get("hourly_rate"),
        years_experience=doc.get("yearsExperience"),
        languages=doc.get("languages", []),
        verified=doc.get("verified", False),
        rating=doc.get("rating"),
        num_reviews=doc.get("numReviews") or doc.get("num_reviews"),
        created_at=doc.get("createdAt") or doc.get("created_at"),
        updated_at=doc.get("updatedAt") or doc.get("updated_at"),
    )


def lawyer_model_to_firestore(lawyer: Lawyer) -> dict:
    return {
        "displayName": lawyer.display_name,
        "email": lawyer.email,
        "profilePicture": lawyer.profile_picture,
        "bio": lawyer.bio,
        "location": lawyer.location,
        "licenseNumber": lawyer.license_number,
        "jurisdictions": lawyer.jurisdictions,
        "practiceAreas": lawyer.practice_areas,
        "hourlyRate": lawyer.hourly_rate,
        "yearsExperience": lawyer.years_experience,
        "languages": lawyer.languages,
        "verified": lawyer.verified,
        "rating": lawyer.rating,
        "numReviews": lawyer.num_reviews,
        "createdAt": lawyer.created_at,
        "updatedAt": lawyer.updated_at,
    }
