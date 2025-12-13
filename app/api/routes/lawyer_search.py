"""
Lawyer search endpoint
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services import firebase_service
from app.dependencies import get_current_user
from app.schemas.lawyer import LawyerProfile, LawyerListResponse

router = APIRouter(prefix="/api/v1/lawyers", tags=["lawyers"])

@router.get("/search", response_model=LawyerListResponse)
async def search_lawyers(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Search for lawyers by name, specialization, or location
    """
    try:
        # For now, implement basic search by querying all lawyers
        # In production, use Firestore text search or Algolia
        docs, total = await firebase_service.query_collection(
            "lawyers", 
            filters={}, 
            limit=page_size * 3,  # Get more to filter
            offset=0
        )
        
        search_term = q.lower()
        lawyers = []
        
        for doc_id, doc in docs:
            # Basic search matching
            name = (doc.get("displayName") or "").lower()
            areas = [area.lower() for area in doc.get("practiceAreas", [])]
            location = (doc.get("location") or "").lower()
            
            if (search_term in name or 
                any(search_term in area for area in areas) or
                search_term in location):
                
                from app.models.lawyer import firestore_lawyer_to_model
                try:
                    model = firestore_lawyer_to_model(doc, doc_id)
                    lawyers.append(LawyerProfile.model_validate(model.model_dump()))
                except Exception:
                    continue
            
            if len(lawyers) >= page_size:
                break
        
        return LawyerListResponse(
            lawyers=lawyers[:page_size],
            total=len(lawyers),
            page=page,
            pageSize=page_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
