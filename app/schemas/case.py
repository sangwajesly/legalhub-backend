"""
Case Schemas for LegalHub Backend

This module defines Pydantic schemas for case-related API endpoints.
Schemas are used for request/response validation and OpenAPI documentation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
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
    is_anonymous: bool = Field(default=False, alias="isAnonymous")
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = Field(None, alias="contactName")
    tags: List[str] = Field(default_factory=list, max_length=10)
    priority: str = Field(default="medium")
    legal_basis: Optional[str] = Field(None, alias="legalBasis")

    model_config = ConfigDict(populate_by_name=True)


class CaseUpdateSchema(BaseModel):
    """Schema for updating a case"""

    category: Optional[CaseCategory] = None
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=5000)
    location: Optional[CaseLocation] = None
    tags: Optional[List[str]] = Field(None, max_length=10)
    priority: Optional[str] = None
    legal_basis: Optional[str] = Field(None, alias="legalBasis")

    model_config = ConfigDict(populate_by_name=True)


class CaseStatusUpdateSchema(BaseModel):
    """Schema for updating case status"""

    status: CaseStatus
    notes: Optional[str] = Field(None, max_length=2000)
    assigned_to: Optional[str] = Field(None, alias="assignedTo")

    model_config = ConfigDict(populate_by_name=True)


class CaseDetailSchema(BaseModel):
    """Schema for case detail response"""

    case_id: str = Field(..., alias="caseId")
    user_id: Optional[str] = Field(None, alias="userId")
    is_anonymous: bool = Field(..., alias="isAnonymous")
    category: CaseCategory
    title: str
    description: str
    location: Optional[CaseLocation]
    email: Optional[str]
    phone: Optional[str]
    contact_name: Optional[str] = Field(None, alias="contactName")
    status: CaseStatus
    priority: str
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    attachments: List[CaseAttachment]
    tags: List[str]
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    resolved_at: Optional[datetime] = Field(None, alias="resolvedAt")
    legal_basis: Optional[str] = Field(None, alias="legalBasis")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class CaseListSchema(BaseModel):
    """Schema for case list response"""

    cases: List[CaseDetailSchema]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class AttachmentUploadSchema(BaseModel):
    """Schema for file attachment metadata"""

    file_name: str = Field(..., alias="fileName")
    file_type: str = Field(..., alias="fileType")
    file_size: int = Field(..., alias="fileSize")

    model_config = ConfigDict(populate_by_name=True)
