"""
Case Models for LegalHub Backend

This module defines the Case and related models that represent
case data stored in Firebase Firestore for both anonymous and identified reporting.
"""

from datetime import datetime, timezone
from typing import Optional, List, Literal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# Helper function for timezone-aware UTC datetime
def utc_now():
    """Get current UTC datetime (timezone-aware)"""
    return datetime.now(timezone.utc)


class CaseStatus(str, Enum):
    """Case status enumeration"""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class CaseCategory(str, Enum):
    """Case category enumeration"""

    CIVIL = "civil"
    CRIMINAL = "criminal"
    FAMILY = "family"
    LABOR = "labor"
    COMMERCIAL = "commercial"
    PROPERTY = "property"
    CONSTITUTIONAL = "constitutional"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"


class CaseAttachment(BaseModel):
    """
    Attachment model for case evidence and documents
    """

    attachment_id: str = Field(
        ..., description="Unique attachment identifier", alias="attachmentId")
    file_name: str = Field(...,
                           description="Original filename", alias="fileName")
    file_url: str = Field(...,
                          description="Firebase Storage URL to the file", alias="fileUrl")
    file_type: str = Field(
        ..., description="MIME type (e.g., image/jpeg, application/pdf)", alias="fileType"
    )
    file_size: int = Field(...,
                           description="File size in bytes", alias="fileSize")
    uploaded_at: datetime = Field(
        default_factory=utc_now, description="Upload timestamp", alias="uploadedAt"
    )
    uploaded_by: Optional[str] = Field(
        default=None, description="UID of uploader (None if anonymous)", alias="uploadedBy"
    )

    model_config = ConfigDict(populate_by_name=True)


class CaseLocation(BaseModel):
    """
    Location model for case geolocation data
    """

    latitude: Optional[float] = Field(
        default=None, description="Geographic latitude")
    longitude: Optional[float] = Field(
        default=None, description="Geographic longitude")
    address: Optional[str] = Field(
        default=None, max_length=500, description="Full address"
    )
    city: Optional[str] = Field(default=None, description="City name")
    region: Optional[str] = Field(
        default=None, description="State/Province/Region")
    country: Optional[str] = Field(default=None, description="Country name")
    postal_code: Optional[str] = Field(
        default=None, description="Postal code", alias="postalCode")

    model_config = ConfigDict(populate_by_name=True)


class CaseBase(BaseModel):
    """Base case model with common fields"""

    category: CaseCategory = Field(..., description="Category of the case")
    title: str = Field(
        ..., min_length=5, max_length=200, description="Short title of the case"
    )
    description: str = Field(
        ..., min_length=20, max_length=5000, description="Detailed case description"
    )
    location: Optional[CaseLocation] = Field(
        default=None, description="Location information"
    )
    tags: List[str] = Field(
        default_factory=list, max_length=10, description="Case tags for categorization"
    )

    model_config = ConfigDict(populate_by_name=True)


class Case(CaseBase):
    """
    Complete Case model representing a case in Firestore

    Collection: cases/
    Document ID: caseId (auto-generated)
    """

    case_id: str = Field(...,
                         description="Unique case identifier", alias="caseId")
    user_id: Optional[str] = Field(
        default=None, description="Firebase UID of reporter (None if anonymous)", alias="userId"
    )
    is_anonymous: bool = Field(
        default=False, description="Whether the case is reported anonymously", alias="isAnonymous"
    )

    # Contact information (optional for anonymous cases)
    email: Optional[str] = Field(
        default=None, description="Reporter's email address")
    phone: Optional[str] = Field(
        default=None, description="Reporter's phone number")
    contact_name: Optional[str] = Field(
        default=None, description="Name of the person reporting", alias="contactName"
    )

    # Case status and management
    status: CaseStatus = Field(
        default=CaseStatus.SUBMITTED, description="Current case status"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Case priority level"
    )

    # Assignment and handling
    assigned_to: Optional[str] = Field(
        default=None, description="UID of assigned lawyer/handler", alias="assignedTo"
    )
    assigned_at: Optional[datetime] = Field(
        default=None, description="When the case was assigned", alias="assignedAt"
    )

    # Attachments and evidence
    attachments: List[CaseAttachment] = Field(
        default_factory=list, description="List of uploaded evidence files"
    )

    # Case timeline
    created_at: datetime = Field(
        default_factory=utc_now, description="Case submission timestamp", alias="createdAt"
    )
    updated_at: datetime = Field(
        default_factory=utc_now, description="Last update timestamp", alias="updatedAt"
    )
    resolved_at: Optional[datetime] = Field(
        default=None, description="Case resolution timestamp", alias="resolvedAt"
    )
    closed_at: Optional[datetime] = Field(
        default=None, description="Case closure timestamp", alias="closedAt"
    )

    # Additional metadata
    view_count: int = Field(
        default=0, description="Number of times case has been viewed", alias="viewCount"
    )
    is_encrypted: bool = Field(
        default=True, description="Whether case data is encrypted", alias="isEncrypted"
    )
    encryption_key: Optional[str] = Field(
        default=None, description="Encryption key reference (for encrypted cases)", alias="encryptionKey"
    )

    # Legal relevance
    legal_basis: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Legal basis or statute relevant to the case",
        alias="legalBasis"
    )

    # Status update notes
    status_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Internal notes about case status changes",
        alias="statusNotes"
    )

    # Analytics and tracking
    has_notified: bool = Field(
        default=False, description="Whether reporter has been notified of status change", alias="hasNotified"
    )
    last_notification_at: Optional[datetime] = Field(
        default=None, description="Last notification timestamp", alias="lastNotificationAt"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "caseId": "case_123456",
                "userId": None,
                "isAnonymous": True,
                "category": "criminal",
                "title": "Workplace discrimination case",
                "description": "Experienced racial discrimination at workplace...",
                "location": {
                    "city": "Bamenda",
                    "region": "Northwest",
                    "country": "Cameroon",
                    "address": "123 Main Street, Bamenda",
                },
                "email": "reporter@example.com",
                "phone": "+237123456789",
                "contactName": "John Doe",
                "status": "submitted",
                "priority": "high",
                "attachments": [],
                "tags": ["discrimination", "workplace", "urgent"],
                "createdAt": "2024-01-15T10:30:00",
                "updatedAt": "2024-01-15T10:30:00",
                "legalBasis": "International Labour Organization Convention No. 111",
            }
        }
    )


class CaseCreateRequest(CaseBase):
    """
    Request model for creating a new case

    Used in POST /api/cases endpoint.
    Either userId or anonymous contact information should be provided.
    """

    is_anonymous: bool = Field(
        default=False, description="Whether to report anonymously", alias="isAnonymous"
    )
    email: Optional[str] = Field(
        default=None, description="Contact email (required if anonymous)"
    )
    phone: Optional[str] = Field(
        default=None, description="Contact phone (optional)")
    contact_name: Optional[str] = Field(
        default=None, description="Name (required if anonymous)", alias="contactName"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Initial priority level"
    )
    legal_basis: Optional[str] = Field(
        default=None, description="Relevant legal statute or basis", alias="legalBasis"
    )


class CaseUpdateRequest(BaseModel):
    """
    Request model for updating a case

    Used in PUT /api/cases/{id} endpoint.
    All fields are optional.
    """

    category: Optional[CaseCategory] = None
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=5000)
    location: Optional[CaseLocation] = None
    tags: Optional[List[str]] = Field(None, max_length=10)
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    legal_basis: Optional[str] = Field(
        None, max_length=1000, alias="legalBasis")

    model_config = ConfigDict(populate_by_name=True)


class CaseStatusUpdateRequest(BaseModel):
    """
    Request model for updating case status

    Used in PUT /api/cases/{id}/status endpoint.
    """

    status: CaseStatus = Field(..., description="New case status")
    notes: Optional[str] = Field(
        None, max_length=2000, description="Status update notes"
    )
    assigned_to: Optional[str] = Field(
        None, description="UID of handler/lawyer to assign", alias="assignedTo"
    )

    model_config = ConfigDict(populate_by_name=True)


class CaseResponse(Case):
    """
    Response model for case endpoints

    This is the public-facing version of the Case model.
    Sensitive fields like encryption keys are excluded.
    """

    # Hide sensitive fields in response
    encryption_key: Optional[str] = Field(
        default=None, exclude=True, alias="encryptionKey")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "caseId": "case_123456",
                "userId": None,
                "isAnonymous": True,
                "category": "criminal",
                "title": "Workplace discrimination case",
                "description": "Experienced racial discrimination at workplace...",
                "status": "under_review",
                "priority": "high",
                "createdAt": "2024-01-15T10:30:00",
            }
        }
    )


class CaseListResponse(BaseModel):
    """Response model for listing cases"""

    cases: List[CaseResponse] = Field(..., description="List of cases")
    total: int = Field(..., description="Total count of cases")
    page: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Page size", alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class CaseDetailResponse(CaseResponse):
    """
    Detailed response model for a single case

    Includes all case information and attachments.
    """

    attachments: List[CaseAttachment] = Field(
        default_factory=list, description="Case evidence and attachments"
    )


class CaseStats(BaseModel):
    """
    Case statistics and analytics model

    Can be stored as a separate document or calculated on-demand.
    """

    total_cases: int = Field(
        default=0, description="Total number of cases", alias="totalCases")
    total_anonymous_cases: int = Field(
        default=0, description="Total anonymous cases", alias="totalAnonymousCases")
    total_identified_cases: int = Field(
        default=0, description="Total identified cases", alias="totalIdentifiedCases")

    cases_by_category: dict = Field(
        default_factory=dict, description="Cases grouped by category", alias="casesByCategory"
    )
    cases_by_status: dict = Field(
        default_factory=dict, description="Cases grouped by status", alias="casesByStatus"
    )
    cases_by_priority: dict = Field(
        default_factory=dict, description="Cases grouped by priority", alias="casesByPriority"
    )

    average_resolution_time: Optional[float] = Field(
        default=None, description="Average time to resolve cases in days", alias="averageResolutionTime"
    )
    pending_cases: int = Field(
        default=0, description="Currently pending cases", alias="pendingCases")
    resolved_cases: int = Field(
        default=0, description="Total resolved cases", alias="resolvedCases")

    cases_by_location: dict = Field(
        default_factory=dict, description="Cases grouped by location/country", alias="casesByLocation"
    )

    last_updated_at: datetime = Field(
        default_factory=utc_now, description="Last stats update", alias="lastUpdatedAt"
    )

    model_config = ConfigDict(populate_by_name=True)


# Helper function to convert Firestore document to Case model
def firestore_case_to_model(doc_data: dict, case_id: str) -> Case:
    return Case.model_validate({**doc_data, "caseId": case_id})


# Helper function to convert Case model to Firestore document
def case_model_to_firestore(case: Case) -> dict:
    data = case.model_dump(by_alias=True)
    data.pop("caseId", None)
    return data
