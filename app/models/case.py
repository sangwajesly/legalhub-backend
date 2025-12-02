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

    Attributes:
        attachmentId: Unique identifier for the attachment
        fileName: Original filename of the attachment
        fileUrl: Firebase Storage URL to the file
        fileType: MIME type of the file
        fileSize: Size of the file in bytes
        uploadedAt: Timestamp when the file was uploaded
        uploadedBy: UID of the user who uploaded the file
    """

    attachmentId: str = Field(..., description="Unique attachment identifier")
    fileName: str = Field(..., description="Original filename")
    fileUrl: str = Field(..., description="Firebase Storage URL to the file")
    fileType: str = Field(
        ..., description="MIME type (e.g., image/jpeg, application/pdf)"
    )
    fileSize: int = Field(..., description="File size in bytes")
    uploadedAt: datetime = Field(
        default_factory=utc_now, description="Upload timestamp"
    )
    uploadedBy: Optional[str] = Field(
        default=None, description="UID of uploader (None if anonymous)"
    )


class CaseLocation(BaseModel):
    """
    Location model for case geolocation data

    Attributes:
        latitude: Geographic latitude
        longitude: Geographic longitude
        address: Human-readable address
        city: City name
        region: State/Province/Region
        country: Country name
        postalCode: Postal code
    """

    latitude: Optional[float] = Field(default=None, description="Geographic latitude")
    longitude: Optional[float] = Field(default=None, description="Geographic longitude")
    address: Optional[str] = Field(
        default=None, max_length=500, description="Full address"
    )
    city: Optional[str] = Field(default=None, description="City name")
    region: Optional[str] = Field(default=None, description="State/Province/Region")
    country: Optional[str] = Field(default=None, description="Country name")
    postalCode: Optional[str] = Field(default=None, description="Postal code")


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


class Case(CaseBase):
    """
    Complete Case model representing a case in Firestore

    Supports both anonymous and identified case submissions.

    Collection: cases/
    Document ID: caseId (auto-generated)
    """

    caseId: str = Field(..., description="Unique case identifier")
    userId: Optional[str] = Field(
        default=None, description="Firebase UID of reporter (None if anonymous)"
    )
    isAnonymous: bool = Field(
        default=False, description="Whether the case is reported anonymously"
    )

    # Contact information (optional for anonymous cases)
    email: Optional[str] = Field(default=None, description="Reporter's email address")
    phone: Optional[str] = Field(default=None, description="Reporter's phone number")
    contactName: Optional[str] = Field(
        default=None, description="Name of the person reporting"
    )

    # Case status and management
    status: CaseStatus = Field(
        default=CaseStatus.SUBMITTED, description="Current case status"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Case priority level"
    )

    # Assignment and handling
    assignedTo: Optional[str] = Field(
        default=None, description="UID of assigned lawyer/handler"
    )
    assignedAt: Optional[datetime] = Field(
        default=None, description="When the case was assigned"
    )

    # Attachments and evidence
    attachments: List[CaseAttachment] = Field(
        default_factory=list, description="List of uploaded evidence files"
    )

    # Case timeline
    createdAt: datetime = Field(
        default_factory=utc_now, description="Case submission timestamp"
    )
    updatedAt: datetime = Field(
        default_factory=utc_now, description="Last update timestamp"
    )
    resolvedAt: Optional[datetime] = Field(
        default=None, description="Case resolution timestamp"
    )
    closedAt: Optional[datetime] = Field(
        default=None, description="Case closure timestamp"
    )

    # Additional metadata
    viewCount: int = Field(
        default=0, description="Number of times case has been viewed"
    )
    isEncrypted: bool = Field(
        default=True, description="Whether case data is encrypted"
    )
    encryptionKey: Optional[str] = Field(
        default=None, description="Encryption key reference (for encrypted cases)"
    )

    # Legal relevance
    legalBasis: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Legal basis or statute relevant to the case",
    )

    # Status update notes
    statusNotes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Internal notes about case status changes",
    )

    # Analytics and tracking
    hasNotified: bool = Field(
        default=False, description="Whether reporter has been notified of status change"
    )
    lastNotificationAt: Optional[datetime] = Field(
        default=None, description="Last notification timestamp"
    )

    model_config = ConfigDict(
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

    isAnonymous: bool = Field(
        default=False, description="Whether to report anonymously"
    )
    email: Optional[str] = Field(
        default=None, description="Contact email (required if anonymous)"
    )
    phone: Optional[str] = Field(default=None, description="Contact phone (optional)")
    contactName: Optional[str] = Field(
        default=None, description="Name (required if anonymous)"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Initial priority level"
    )
    legalBasis: Optional[str] = Field(
        default=None, description="Relevant legal statute or basis"
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
    legalBasis: Optional[str] = Field(None, max_length=1000)


class CaseStatusUpdateRequest(BaseModel):
    """
    Request model for updating case status

    Used in PUT /api/cases/{id}/status endpoint.
    """

    status: CaseStatus = Field(..., description="New case status")
    notes: Optional[str] = Field(
        None, max_length=2000, description="Status update notes"
    )
    assignedTo: Optional[str] = Field(
        None, description="UID of handler/lawyer to assign"
    )


class CaseResponse(Case):
    """
    Response model for case endpoints

    This is the public-facing version of the Case model.
    Sensitive fields like encryption keys are excluded.
    """

    # Hide sensitive fields in response
    encryptionKey: Optional[str] = Field(default=None, exclude=True)

    model_config = ConfigDict(
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
    pageSize: int = Field(..., description="Page size")


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

    totalCases: int = Field(default=0, description="Total number of cases")
    totalAnonymousCases: int = Field(default=0, description="Total anonymous cases")
    totalIdentifiedCases: int = Field(default=0, description="Total identified cases")

    casesByCategory: dict = Field(
        default_factory=dict, description="Cases grouped by category"
    )
    casesByStatus: dict = Field(
        default_factory=dict, description="Cases grouped by status"
    )
    casesByPriority: dict = Field(
        default_factory=dict, description="Cases grouped by priority"
    )

    averageResolutionTime: Optional[float] = Field(
        default=None, description="Average time to resolve cases in days"
    )
    pendingCases: int = Field(default=0, description="Currently pending cases")
    resolvedCases: int = Field(default=0, description="Total resolved cases")

    casesByLocation: dict = Field(
        default_factory=dict, description="Cases grouped by location/country"
    )

    lastUpdatedAt: datetime = Field(
        default_factory=utc_now, description="Last stats update"
    )


# Helper function to convert Firestore document to Case model
def firestore_case_to_model(doc_data: dict, caseId: str) -> Case:
    """
    Convert Firestore document data to Case model

    Args:
        doc_data: Dictionary from Firestore document
        caseId: Case ID

    Returns:
        Case model instance
    """
    # Parse attachments
    attachments = []
    if "attachments" in doc_data and doc_data["attachments"]:
        attachments = [CaseAttachment(**att) for att in doc_data["attachments"]]

    # Parse location
    location = None
    if "location" in doc_data and doc_data["location"]:
        location = CaseLocation(**doc_data["location"])

    return Case(
        caseId=caseId,
        userId=doc_data.get("userId"),
        isAnonymous=doc_data.get("isAnonymous", False),
        category=doc_data.get("category", "other"),
        title=doc_data.get("title"),
        description=doc_data.get("description"),
        location=location,
        email=doc_data.get("email"),
        phone=doc_data.get("phone"),
        contactName=doc_data.get("contactName"),
        status=doc_data.get("status", "submitted"),
        priority=doc_data.get("priority", "medium"),
        assignedTo=doc_data.get("assignedTo"),
        assignedAt=doc_data.get("assignedAt"),
        attachments=attachments,
        tags=doc_data.get("tags", []),
        createdAt=doc_data.get("createdAt"),
        updatedAt=doc_data.get("updatedAt"),
        resolvedAt=doc_data.get("resolvedAt"),
        closedAt=doc_data.get("closedAt"),
        viewCount=doc_data.get("viewCount", 0),
        isEncrypted=doc_data.get("isEncrypted", True),
        encryptionKey=doc_data.get("encryptionKey"),
        legalBasis=doc_data.get("legalBasis"),
        statusNotes=doc_data.get("statusNotes"),
        hasNotified=doc_data.get("hasNotified", False),
        lastNotificationAt=doc_data.get("lastNotificationAt"),
    )


# Helper function to convert Case model to Firestore document
def case_model_to_firestore(case: Case) -> dict:
    """
    Convert Case model to Firestore document format

    Args:
        case: Case model instance

    Returns:
        Dictionary for Firestore storage
    """
    return {
        "userId": case.userId,
        "isAnonymous": case.isAnonymous,
        "category": case.category.value,
        "title": case.title,
        "description": case.description,
        "location": case.location.model_dump() if case.location else None,
        "email": case.email,
        "phone": case.phone,
        "contactName": case.contactName,
        "status": case.status.value,
        "priority": case.priority,
        "assignedTo": case.assignedTo,
        "assignedAt": case.assignedAt,
        "attachments": [att.model_dump() for att in case.attachments],
        "tags": case.tags,
        "createdAt": case.createdAt,
        "updatedAt": case.updatedAt,
        "resolvedAt": case.resolvedAt,
        "closedAt": case.closedAt,
        "viewCount": case.viewCount,
        "isEncrypted": case.isEncrypted,
        "encryptionKey": case.encryptionKey,
        "legalBasis": case.legalBasis,
        "statusNotes": case.statusNotes,
        "hasNotified": case.hasNotified,
        "lastNotificationAt": case.lastNotificationAt,
    }
