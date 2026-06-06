"""
Case Schemas for LegalHub Backend

This module defines Pydantic schemas for case-related API endpoints.
Schemas are used for request/response validation and OpenAPI documentation.
"""

from typing import Optional, List, Union, Literal, ClassVar
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
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
    location: Optional[Union[CaseLocation, str]] = None
    is_anonymous: bool = Field(default=False, alias="isAnonymous")
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = Field(None, alias="contactName")
    tags: List[str] = Field(default_factory=list, max_length=10)
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium")
    legal_basis: Optional[str] = Field(None, alias="legalBasis")
    jurisdiction: Optional[str] = Field(None, max_length=200, description="Legal jurisdiction applicable to the case")

    CATEGORY_MAP: ClassVar[dict[str, str]] = {
        "civil": "civil",
        "criminal": "criminal",
        "family": "family",
        "family law": "family",
        "labor": "labor",
        "labour": "labor",
        "commercial": "commercial",
        "property": "property",
        "constitutional": "constitutional",
        "administrative": "administrative",
        "other": "other",
    }

    PRIORITY_MAP: ClassVar[dict[str, str]] = {
        "low": "low",
        "medium": "medium",
        "normal": "medium",
        "high": "high",
        "critical": "critical",
    }

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            return cls.CATEGORY_MAP.get(normalized, normalized)
        return value

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, value):
        if isinstance(value, str):
            return {"address": value}
        return value

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            return cls.PRIORITY_MAP.get(normalized, normalized)
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    @classmethod
    def validate_anonymous_submission(cls, case):
        if case.is_anonymous and (not case.email or not case.contact_name):
            raise ValueError(
                "Email and contactName are required for anonymous submissions"
            )
        return case

    model_config = ConfigDict(populate_by_name=True)


class CaseUpdateSchema(BaseModel):
    """Schema for updating a case"""

    category: Optional[CaseCategory] = None
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=5000)
    location: Optional[Union[CaseLocation, str]] = None
    tags: Optional[List[str]] = Field(None, max_length=10)
    priority: Optional[str] = None
    legal_basis: Optional[str] = Field(None, alias="legalBasis")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, value):
        if isinstance(value, str):
            return {"address": value}
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

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
