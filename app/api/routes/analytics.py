"""Analytics endpoints: overview and simple aggregations"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
from collections import Counter
from datetime import datetime, timezone, timedelta

from app.services.firebase_service import firebase_service
from app.schemas.analytics import OverviewResponse, CasesByStatusResponse
from app.dependencies import require_roles
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
