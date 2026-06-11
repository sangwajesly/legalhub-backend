"""
Lawyer profile and bookings routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.services.firebase_service import firebase_service
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingResponse, BookingListSchema, BookingStatusSchema, BookingDetailSchema
from app.schemas.lawyer import LawyerProfile, LawyerListResponse, LawyerCreate, LawyerUpdate
from app.dependencies import require_lawyer, require_admin, get_optional_user, require_roles, get_current_user
from app.models.lawyer import Lawyer, lawyer_model_to_firestore, firestore_lawyer_to_model

router = APIRouter(prefix="/api/v1/lawyers", tags=["Lawyers"])


@router.get("", response_model=LawyerListResponse, response_model_by_alias=False)
async def list_lawyers(
    q: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all lawyers with filtering.
    Non-admins only see verified lawyers.
    """
    try:
        # Build filters
        filters = {}
        
        # Only show verified unless it's an admin checking
        is_admin = current_user and current_user.role == "admin"
        if not is_admin:
            filters["verified"] = True

        # Fetch lawyers from database
        docs, total = await firebase_service.query_collection(
            "lawyers",
            filters=filters,
            limit=page_size * 5,  # Fetch more to allow in-memory filtering if needed
            offset=0
        )
        
        lawyers_list = []
        from app.models.lawyer import firestore_lawyer_to_model
        
        search_term = q.lower() if q else None
        spec_term = specialization.lower() if specialization else None
        loc_term = location.lower() if location else None
        
        for doc_id, doc in docs:
            # Parse model
            try:
                model = firestore_lawyer_to_model(doc, doc_id)
            except Exception:
                continue
                
            # Filter in-memory for specialization / location / search query
            if search_term:
                name = (model.display_name or "").lower()
                bio = (model.bio or "").lower()
                loc = (model.location or "").lower()
                areas = [a.lower() for a in model.practice_areas]
                if not (search_term in name or search_term in bio or search_term in loc or any(search_term in a for a in areas)):
                    continue
                    
            if spec_term:
                areas = [a.lower() for a in model.practice_areas]
                if not any(spec_term in a for a in areas):
                    continue
                    
            if loc_term:
                loc = (model.location or "").lower()
                if loc_term not in loc:
                    continue
                    
            lawyers_list.append(LawyerProfile.model_validate(model.model_dump()))
            
        # Paginate results in memory
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_lawyers = lawyers_list[start_idx:end_idx]
        
        return LawyerListResponse(
            lawyers=paginated_lawyers,
            total=len(lawyers_list),
            page=page,
            pageSize=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list lawyers: {str(e)}"
        )


@router.get("/search", response_model=LawyerListResponse, response_model_by_alias=False)
async def search_lawyers(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Search for verified lawyers by query matching name, specialization, or location.
    """
    return await list_lawyers(q=q, page=page, page_size=page_size)


@router.get("/pending", response_model=LawyerListResponse, response_model_by_alias=False)
async def list_pending_lawyers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin)
):
    """
    List all lawyers pending manual verification (Admin only).
    """
    try:
        docs, total = await firebase_service.query_collection(
            "lawyers",
            filters={"verified": False},
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        lawyers_list = []
        from app.models.lawyer import firestore_lawyer_to_model
        for doc_id, doc in docs:
            try:
                model = firestore_lawyer_to_model(doc, doc_id)
                lawyers_list.append(LawyerProfile.model_validate(model.model_dump()))
            except Exception:
                continue
                
        return LawyerListResponse(
            lawyers=lawyers_list,
            total=total,
            page=page,
            pageSize=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list pending lawyers: {str(e)}"
        )


@router.put("/{lawyer_id}/verify", response_model=LawyerProfile, response_model_by_alias=False)
async def verify_lawyer(
    lawyer_id: str,
    verified: bool = Query(True),
    current_user: User = Depends(require_admin)
):
    """
    Verify or unverify a lawyer profile (Admin only).
    """
    try:
        # Check if lawyer exists
        doc = await firebase_service.get_document(f"lawyers/{lawyer_id}")
        if not doc:
            raise HTTPException(status_code=404, detail="Lawyer profile not found")
            
        # Update verified field
        await firebase_service.update_document(f"lawyers/{lawyer_id}", {
            "verified": verified,
            "updatedAt": datetime.now(timezone.utc)
        })
        
        # Fetch updated profile
        updated_doc = await firebase_service.get_document(f"lawyers/{lawyer_id}")
        from app.models.lawyer import firestore_lawyer_to_model
        model = firestore_lawyer_to_model(updated_doc, lawyer_id)
        
        return LawyerProfile.model_validate(model.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify lawyer: {str(e)}"
        )


@router.get("/{lawyer_id}", response_model=LawyerProfile, response_model_by_alias=False)
async def get_lawyer_profile(
    lawyer_id: str
):
    """
    Get a lawyer's profile details.
    """
    try:
        doc = await firebase_service.get_document(f"lawyers/{lawyer_id}")
        if not doc:
            raise HTTPException(status_code=404, detail="Lawyer profile not found")
            
        from app.models.lawyer import firestore_lawyer_to_model
        model = firestore_lawyer_to_model(doc, lawyer_id)
        return LawyerProfile.model_validate(model.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve lawyer profile: {str(e)}"
        )


@router.post("", response_model=LawyerProfile, response_model_by_alias=False)
async def create_or_update_lawyer(
    data: LawyerCreate, current_user: Optional[Any] = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if isinstance(current_user, dict):
        uid = current_user.get("uid")
    else:
        uid = current_user.uid

    # Build a lawyer model from provided data and defaults
    lawyer = Lawyer(
        uid=uid,
        displayName=data.display_name,
        email=data.email,
        bio=data.bio,
        location=data.location,
        licenseNumber=data.license_number,
        practiceAreas=data.practice_areas or [],
        hourlyRate=data.hourly_rate,
        verified=False,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    firestore_doc = lawyer_model_to_firestore(lawyer)
    await firebase_service.set_document(f"lawyers/{uid}", firestore_doc)
    doc = await firebase_service.get_document(f"lawyers/{uid}")
    if not doc:
        raise HTTPException(status_code=404, detail="Failed to retrieve created lawyer profile")
    return LawyerProfile.model_validate(
        firestore_lawyer_to_model(doc, uid).model_dump()
    )


@router.put("/{lawyer_id}", response_model=LawyerProfile, response_model_by_alias=False)
async def update_lawyer_profile_endpoint(
    lawyer_id: str,
    data: LawyerUpdate,
    current_user: Optional[Any] = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if isinstance(current_user, dict):
        uid = current_user.get("uid")
        is_admin = current_user.get("is_admin")
    else:
        uid = current_user.uid
        is_admin = current_user.role == "admin" or getattr(current_user, "is_admin", False)

    if uid != lawyer_id and not is_admin:
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
    if data.license_number is not None:
        if not is_admin:
            existing_license = doc.get("licenseNumber") or doc.get("license_number")
            # Normalize None/null and empty strings to "" for comparison
            normalized_new = data.license_number.strip() if data.license_number else ""
            normalized_existing = existing_license.strip() if existing_license else ""
            if normalized_new != normalized_existing:
                raise HTTPException(
                    status_code=403,
                    detail="Lawyers cannot update their own license number. Please contact support."
                )
        else:
            update_fields["licenseNumber"] = data.license_number
    if data.years_experience is not None:
        update_fields["yearsExperience"] = data.years_experience
    if data.verified is not None:
        update_fields["verified"] = data.verified

    update_fields["updatedAt"] = datetime.now(timezone.utc)

    await firebase_service.update_document(f"lawyers/{lawyer_id}", update_fields)
    updated = await firebase_service.get_document(f"lawyers/{lawyer_id}")
    return LawyerProfile.model_validate(
        firestore_lawyer_to_model(updated, lawyer_id).model_dump()
    )


@router.delete("/{lawyer_id}")
async def delete_lawyer_profile_endpoint(
    lawyer_id: str, current_user: Optional[Any] = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if isinstance(current_user, dict):
        uid = current_user.get("uid")
        is_admin = current_user.get("is_admin")
    else:
        uid = current_user.uid
        is_admin = current_user.role == "admin" or getattr(current_user, "is_admin", False)

    if uid != lawyer_id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this profile"
        )

    doc = await firebase_service.get_document(f"lawyers/{lawyer_id}")
    if not doc:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    await firebase_service.delete_document(f"lawyers/{lawyer_id}")
    return {"ok": True}


@router.get(
    "/{lawyer_id}/bookings",
    response_model=BookingListSchema,
    summary="Retrieve a list of bookings for a specific lawyer",
    response_description="A list of booking details for the specified lawyer"
)
async def get_lawyer_bookings_route(
    lawyer_id: str,
    status: Optional[BookingStatus] = None,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(require_lawyer),
):
    """
    Retrieves a paginated list of bookings for the authenticated lawyer.
    """
    if current_user.uid != lawyer_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view bookings for this lawyer."
        )

    bookings = await firebase_service.get_lawyer_bookings(
        lawyer_uid=lawyer_id,
        status=status,
        limit=limit,
        offset=offset
    )

    enriched_bookings = []
    for b in bookings:
        b_dict = b.model_dump()
        try:
            client = await firebase_service.get_user_by_uid(b.user_id)
            if client:
                b_dict["clientName"] = client.display_name
                b_dict["clientEmail"] = client.email
        except Exception as e:
            print(f"WARNING: Failed to fetch client details for booking {b.booking_id}: {e}")
        
        enriched_bookings.append(BookingResponse.model_validate(b_dict))

    return BookingListSchema(
        bookings=enriched_bookings,
        total=len(bookings),
        page=offset // limit + 1,
        pageSize=limit
    )


@router.get(
    "/bookings/{booking_id}",
    response_model=BookingDetailSchema,
    summary="Retrieve details of a specific booking",
    response_description="Detailed information about the booking"
)
async def get_lawyer_booking_detail_route(
    booking_id: str,
    current_user: User = Depends(require_lawyer),
):
    """
    Retrieves detailed information for a specific booking.
    """
    booking = await firebase_service.get_booking_by_id(booking_id)

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    
    if booking.lawyer_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this booking"
        )
    
    b_dict = booking.model_dump()
    try:
        client = await firebase_service.get_user_by_uid(booking.user_id)
        if client:
            b_dict["clientName"] = client.display_name
            b_dict["clientEmail"] = client.email
    except Exception as e:
        print(f"WARNING: Failed to fetch client details: {e}")

    return BookingDetailSchema.model_validate(b_dict)


@router.put(
    "/bookings/{booking_id}/status",
    response_model=BookingDetailSchema,
    summary="Update the status of a specific booking",
    response_description="The updated booking details"
)
async def update_lawyer_booking_status_route(
    booking_id: str,
    status_update: BookingStatusSchema,
    current_user: User = Depends(require_lawyer),
):
    """
    Allows a lawyer to update the status of a booking (e.g., confirm, cancel).
    """
    existing_booking = await firebase_service.get_booking_by_id(booking_id)

    if not existing_booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    
    if existing_booking.lawyer_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to update this booking"
        )
    
    updated_booking = await firebase_service.update_booking_status(
        booking_id=booking_id,
        new_status=status_update.status,
        cancellation_reason=status_update.cancellation_reason,
        lawyer_notes=status_update.notes
    )

    if not updated_booking:
        raise HTTPException(
            status_code=500,
            detail="Failed to update booking status"
        )
    
    b_dict = updated_booking.model_dump()
    try:
        client = await firebase_service.get_user_by_uid(updated_booking.user_id)
        if client:
            b_dict["clientName"] = client.display_name
            b_dict["clientEmail"] = client.email
    except Exception as e:
        print(f"WARNING: Failed to fetch client details: {e}")

    return BookingDetailSchema.model_validate(b_dict)
