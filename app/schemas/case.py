"""
Case Schemas for LegalHub Backend

This module defines Pydantic schemas for case-related API endpoints.
Schemas are used for request/response validation and OpenAPI documentation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.case import (
    CaseStatus,
    CaseCategory,
    CaseAttachment,
    CaseLocation,
    CaseResponse,
    CaseCreateRequest,
    CaseUpdateRequest,
    CaseStatusUpdateRequest,
)


class CaseCreateSchema(BaseModel):
    """Schema for creating a new case"""
    category: CaseCategory
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    location: Optional[CaseLocation] = None
    isAnonymous: bool = Field(default=False)
    email: Optional[str] = None
    phone: Optional[str] = None
    contactName: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_length=10)
    priority: str = Field(default="medium")
    legalBasis: Optional[str] = None


class CaseUpdateSchema(BaseModel):
    """Schema for updating a case"""
    category: Optional[CaseCategory] = None
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=5000)
    location: Optional[CaseLocation] = None
    tags: Optional[List[str]] = Field(None, max_length=10)
    priority: Optional[str] = None
    legalBasis: Optional[str] = None


class CaseStatusUpdateSchema(BaseModel):
    """Schema for updating case status"""
    status: CaseStatus
    notes: Optional[str] = Field(None, max_length=2000)
    assignedTo: Optional[str] = None


class CaseDetailSchema(BaseModel):
    """Schema for case detail response"""
    caseId: str
    userId: Optional[str]
    isAnonymous: bool
    category: CaseCategory
    title: str
    description: str
    location: Optional[CaseLocation]
    email: Optional[str]
    phone: Optional[str]
    contactName: Optional[str]
    status: CaseStatus
    priority: str
    assignedTo: Optional[str]
    attachments: List[CaseAttachment]
    tags: List[str]
    createdAt: datetime
    updatedAt: datetime
    resolvedAt: Optional[datetime]
    legalBasis: Optional[str]


class CaseListSchema(BaseModel):
    """Schema for case list response"""
    cases: List[CaseDetailSchema]
    total: int
    page: int
    pageSize: int


class AttachmentUploadSchema(BaseModel):
    """Schema for file attachment metadata"""
    fileName: str
    fileType: str
    fileSize: int
