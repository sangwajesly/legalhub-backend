"""Analytics request/response schemas"""

from pydantic import BaseModel, ConfigDict
from typing import Dict, List


class OverviewResponse(BaseModel):
    totalUsers: int
    totalLawyers: int
    totalCases: int
    totalBookings: int
    totalArticles: int

    model_config = ConfigDict()


class CasesByStatusResponse(BaseModel):
    counts: Dict[str, int]

    model_config = ConfigDict()

class LawyerDashboardStats(BaseModel):
    total_views: int
    active_cases: int
    total_reviews: int
    raw_rating: float
    total_bookings: int

    model_config = ConfigDict()


class OrganizationDashboardStats(BaseModel):
    total_views: int
    total_members: int = 0
    verified: bool

    model_config = ConfigDict()
