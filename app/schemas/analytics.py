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
