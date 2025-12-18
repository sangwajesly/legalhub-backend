"""
API Router for Organizations
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone

from app.services import firebase_service
from app.dependencies import get_current_user, get_optional_user
from app.models.organization import (
    Organization,
    firestore_organization_to_model,
    organization_model_to_firestore,
)
from app.schemas.organization import (
    OrganizationProfile,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationListResponse,
)

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    organization_type: Optional[str] = None,
):
    """List organizations with pagination and filtering"""
    # Calculate offset
    offset = (page - 1) * page_size

    # Build filters
    filters = []
    if organization_type:
        filters.append(("organizationType", "==", organization_type))

    # Query Firestore
    docs, total = await firebase_service.query_collection(
        "organizations", filters=filters, limit=page_size, offset=offset
    )

    # Convert to schema
    organizations = [
        OrganizationProfile.model_validate(
            firestore_organization_to_model(data, doc_id))
        for doc_id, data in docs
    ]

    return {
        "organizations": organizations,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.get("/{uid}", response_model=OrganizationProfile)
async def get_organization(uid: str):
    """Get organization by UID"""
    doc = await firebase_service.get_document(f"organizations/{uid}")
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    org_model = firestore_organization_to_model(doc, uid)
    return OrganizationProfile.model_validate(org_model)


@router.post("", response_model=OrganizationProfile)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create organization profile for current user"""
    uid = current_user["uid"]

    # Check if exists
    existing = await firebase_service.get_document(f"organizations/{uid}")
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization profile already exists",
        )

    # Create model
    now = datetime.now(timezone.utc)
    org_model = Organization(
        uid=uid,
        display_name=org_data.display_name,
        email=org_data.email,
        bio=org_data.bio,
        location=org_data.location,
        website=org_data.website,
        registration_number=org_data.registration_number,
        organization_type=org_data.organization_type,
        contact_person=org_data.contact_person,
        created_at=now,
        updated_at=now,
    )

    # Save to Firestore
    data = organization_model_to_firestore(org_model)
    await firebase_service.set_document(f"organizations/{uid}", data)

    return OrganizationProfile.model_validate(org_model)


@router.put("/{uid}", response_model=OrganizationProfile)
async def update_organization(
    uid: str,
    org_update: OrganizationUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update organization profile"""
    # Verify ownership or admin
    if current_user["uid"] != uid and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile",
        )

    # Check existence
    existing = await firebase_service.get_document(f"organizations/{uid}")
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Update fields
    update_data = org_update.model_dump(exclude_unset=True)
    if not update_data:
        # No changes
        org_model = firestore_organization_to_model(existing, uid)
        return org_model

    # Add updated_at
    update_data["updatedAt"] = datetime.now(timezone.utc)

    # Map pydantic fields to firestore fields
    # We need to map snake_case to camelCase manually here or use the helper
    # A cleaner way: Update the model, then converting back to firestore

    current_model = firestore_organization_to_model(existing, uid)
    updated_model = current_model.model_copy(update=update_data)
    updated_model.updated_at = datetime.now(timezone.utc)

    firestore_data = organization_model_to_firestore(updated_model)

    # We only want to update the fields that were changed to avoid overwriting unrelated data
    # But since we have the full model, set_document with merge=True is safer if supported
    # Or just update_document with the specific fields.
    # Let's use update_document with mapped fields

    firestore_update = {}
    if "display_name" in update_data:
        firestore_update["displayName"] = update_data["display_name"]
    if "bio" in update_data:
        firestore_update["bio"] = update_data["bio"]
    if "location" in update_data:
        firestore_update["location"] = update_data["location"]
    if "website" in update_data:
        firestore_update["website"] = update_data["website"]
    if "registration_number" in update_data:
        firestore_update["registrationNumber"] = update_data["registration_number"]
    if "organization_type" in update_data:
        firestore_update["organizationType"] = update_data["organization_type"]
    if "contact_person" in update_data:
        firestore_update["contactPerson"] = update_data["contact_person"]
    firestore_update["updatedAt"] = updated_model.updated_at

    await firebase_service.update_document(f"organizations/{uid}", firestore_update)

    return OrganizationProfile.model_validate(updated_model)


@router.delete("/{uid}")
async def delete_organization(
    uid: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete organization profile"""
    if current_user["uid"] != uid and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this profile",
        )

    await firebase_service.delete_document(f"organizations/{uid}")
    return {"status": "success", "message": "Organization profile deleted"}
