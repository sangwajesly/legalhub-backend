"""Analytics endpoints: overview and simple aggregations"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
from collections import Counter
from datetime import datetime, timezone, timedelta

from app.services.firebase_service import firebase_service
from app.schemas.analytics import (
    OverviewResponse, 
    CasesByStatusResponse,
    LawyerDashboardStats,
    OrganizationDashboardStats
)
from app.dependencies import require_roles, require_lawyer, require_organization
from app.models.user import UserRole

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewResponse)
async def overview(current_user=Depends(require_roles(UserRole.ADMIN))):
    """Return basic counts for the dashboard."""
    db = firebase_service.db

    # Count users
    users_coll = db.collection("users")
    total_users = sum(1 for _ in users_coll.stream())

    # Count lawyers
    lawyers_coll = db.collection("lawyers")
    total_lawyers = sum(1 for _ in lawyers_coll.stream())

    # Count cases
    cases_coll = db.collection("cases")
    total_cases = sum(1 for _ in cases_coll.stream())

    # Count bookings
    bookings_coll = db.collection("bookings")
    total_bookings = sum(1 for _ in bookings_coll.stream())

    # Count articles
    articles_coll = db.collection("articles")
    total_articles = sum(1 for _ in articles_coll.stream())

    return OverviewResponse(
        totalUsers=total_users,
        totalLawyers=total_lawyers,
        totalCases=total_cases,
        totalBookings=total_bookings,
        totalArticles=total_articles,
    )


@router.get("/cases/status", response_model=CasesByStatusResponse)
async def cases_by_status(current_user=Depends(require_roles(UserRole.ADMIN))):
    """Aggregate cases count by status field."""
    db = firebase_service.db
    cases_coll = db.collection("cases")
    counter = Counter()
    for doc in cases_coll.stream():
        data = doc.to_dict()
        status_val = data.get("status", "unknown")
        counter[status_val] += 1

    return CasesByStatusResponse(counts=dict(counter))
    return CasesByStatusResponse(counts=dict(counter))


@router.get("/lawyer", response_model=LawyerDashboardStats)
async def lawyer_stats(current_user=Depends(require_lawyer)):
    """Return dashboard stats for the current lawyer."""
    db = firebase_service.db
    uid = current_user.uid

    # 1. Get Lawyer Profile for rating and reviews
    lawyer_doc = await firebase_service.get_document(f"lawyers/{uid}")
    if not lawyer_doc:
         # Fallback if profile missing
         return LawyerDashboardStats(
             total_views=0, active_cases=0, total_reviews=0, raw_rating=0.0, total_bookings=0
         )
    
    # 2. Count Active Cases (where lawyer_id == uid AND status == 'active')
    # Note: Requires composite index on [lawyer_id, status] in Firestore
    # We will just filter in memory if volume is low, or use a simple query
    cases, _ = await firebase_service.query_collection(
        "cases", filters=[("lawyerId", "==", uid), ("status", "==", "active")]
    )
    active_cases_count = len(cases)

    # 3. Count Bookings
    bookings, _ = await firebase_service.query_collection(
        "bookings", filters=[("lawyerId", "==", uid)]
    )
    total_bookings = len(bookings)

    return LawyerDashboardStats(
        total_views=lawyer_doc.get("views", 0), # Assuming 'views' field exists or will exist
        active_cases=active_cases_count,
        total_reviews=lawyer_doc.get("numReviews", 0) or lawyer_doc.get("num_reviews", 0),
        raw_rating=lawyer_doc.get("rating", 0.0),
        total_bookings=total_bookings,
    )


@router.get("/organization", response_model=OrganizationDashboardStats)
async def organization_stats(current_user=Depends(require_organization)):
    """Return dashboard stats for the current organization."""
    uid = current_user.uid
    org_doc = await firebase_service.get_document(f"organizations/{uid}")
    
    if not org_doc:
        return OrganizationDashboardStats(total_views=0, total_members=0, verified=False)

    return OrganizationDashboardStats(
        total_views=org_doc.get("views", 0),
        total_members=0, # Placeholder for future members feature
        verified=org_doc.get("verified", False),
    )
