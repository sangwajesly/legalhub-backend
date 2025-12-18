"""
Lawyer public endpoints

Endpoints:
- GET /api/lawyers - list lawyers
- GET /api/lawyers/{id} - get lawyer profile
- POST /api/lawyers - create/update lawyer profile (authenticated)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from app.services import firebase_service
from app.dependencies import get_current_user
from app.schemas.lawyer import (
    LawyerProfile,
    LawyerListResponse,
    LawyerCreate,
    LawyerUpdate,
)


router = APIRouter(prefix="/api/v1/lawyers", tags=["lawyers"])


@router.get("", response_model=LawyerListResponse)
async def list_lawyers(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)
):
    docs, total = await firebase_service.query_collection(
        "lawyers", filters={}, limit=page_size, offset=(page - 1) * page_size
    )
    lawyers = []
    for doc_id, doc in docs:
        try:
            m = firestore_lawyer_to_model(doc, doc_id)
            lawyers.append(LawyerProfile.model_validate(m))
        except Exception:
            continue
    return LawyerListResponse(
        lawyers=lawyers, total=total, page=page, page_size=page_size
    )


@router.get("/{lawyer_id}", response_model=LawyerProfile)
async def get_lawyer(lawyer_id: str):
    doc = await firebase_service.get_document(f"lawyers/{lawyer_id}")
    if not doc:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    model = firestore_lawyer_to_model(doc, lawyer_id)
    return LawyerProfile.model_validate(model)


@router.post("", response_model=LawyerProfile)
async def create_or_update_lawyer(
    data: LawyerCreate, current_user: Optional[dict] = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    uid = current_user.get("uid")

    # Build a lawyer model from provided data and defaults
    lawyer = Lawyer(
        uid=uid,
        display_name=data.display_name if hasattr(
            data, "display_name") else None,
        email=data.email if hasattr(data, "email") else None,
        bio=data.bio if hasattr(data, "bio") else None,
        location=data.location if hasattr(data, "location") else None,
        license_number=getattr(data, "license_number", None),
        practice_areas=getattr(data, "practice_areas", []),
        hourly_rate=getattr(data, "hourly_rate", None),
        created_at=utc_now(),
        updated_at=utc_now(),
    )

    firestore_doc = lawyer_model_to_firestore(lawyer)
    await firebase_service.set_document(f"lawyers/{uid}", firestore_doc)
    doc = await firebase_service.get_document(f"lawyers/{uid}")
    return LawyerProfile.model_validate(
        firestore_lawyer_to_model(doc, uid)
    )


@router.put("/{lawyer_id}", response_model=LawyerProfile)
async def update_lawyer(
    lawyer_id: str,
    data: LawyerUpdate,
    current_user: Optional[dict] = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    is_admin = current_user.get("is_admin")
    if current_user.get("uid") != lawyer_id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this profile"
        )

    doc = await firebase_service.get_document(f"lawyers/{lawyer_id}")
    if not doc:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    update_fields = {}
    if data.display_name is not None:
        update_fields["displayName"] = data.display_name
    if data.bio is not None:
        update_fields["bio"] = data.bio
    if data.location is not None:
        update_fields["location"] = data.location
    if data.practice_areas is not None:
        update_fields["practiceAreas"] = data.practice_areas
    if data.hourly_rate is not None:
        update_fields["hourlyRate"] = data.hourly_rate
    if data.verified is not None:
        update_fields["verified"] = data.verified

    update_fields["updatedAt"] = utc_now()

    await firebase_service.update_document(f"lawyers/{lawyer_id}", update_fields)
    updated = await firebase_service.get_document(f"lawyers/{lawyer_id}")
    return LawyerProfile.model_validate(
        firestore_lawyer_to_model(updated, lawyer_id)
    )


@router.delete("/{lawyer_id}")
async def delete_lawyer(
    lawyer_id: str, current_user: Optional[dict] = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    is_admin = current_user.get("is_admin")
    if current_user.get("uid") != lawyer_id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this profile"
        )

    doc = await firebase_service.get_document(f"lawyers/{lawyer_id}")
    if not doc:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    await firebase_service.delete_document(f"lawyers/{lawyer_id}")
    return {"ok": True}
