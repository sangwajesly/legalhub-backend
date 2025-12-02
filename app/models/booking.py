"""
Booking Models for LegalHub Backend

This module defines the Booking models that represent
lawyer consultation bookings in Firebase Firestore.
"""

from datetime import datetime, timezone
from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# Helper function for timezone-aware UTC datetime
def utc_now():
    """Get current UTC datetime (timezone-aware)"""
    return datetime.now(timezone.utc)


def _parse_datetime(value):
    """Parse a datetime-like value into a timezone-aware datetime.

    - If value is already a datetime, return it.
    - If value is a string, attempt fromisoformat and return.
    - If value is None or parsing fails, return current UTC time.
    """
    if value is None:
        return utc_now()
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            try:
                # fallback: let pydantic attempt parsing if needed
                return datetime.fromisoformat(value)
            except Exception:
                return utc_now()
    return utc_now()


class BookingStatus(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"


class ConsultationType(str, Enum):
    """Type of consultation"""
    CALL = "call"  # Phone/video call
    MEETING = "meeting"  # In-person meeting
    CHAT = "chat"  # Text-based consultation
    VIDEO = "video"  # Video call


class BookingBase(BaseModel):
    """Base booking model with common fields"""
    lawyerId: str = Field(..., description="Firebase UID of the lawyer")
    userId: str = Field(..., description="Firebase UID of the client")
    consultationType: ConsultationType = Field(
        default=ConsultationType.CALL,
        description="Type of consultation"
    )
    
    # Scheduling
    scheduledAt: datetime = Field(..., description="Scheduled consultation timestamp")
    duration: int = Field(
        default=30,
        ge=15,
        le=240,
        description="Consultation duration in minutes"
    )
    
    # Location/Contact info
    location: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Meeting location (for in-person) or contact details"
    )
    
    # Description and case details
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Brief description of the consultation topic"
    )
    
    caseId: Optional[str] = Field(
        default=None,
        description="Reference to a case if this booking is related"
    )
    
    # Tags/categories
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Tags for consultation categorization"
    )


class Booking(BookingBase):
    """
    Complete Booking model representing a lawyer consultation booking in Firestore
    
    Collection: bookings/
    Document ID: bookingId (auto-generated)
    """
    bookingId: str = Field(..., description="Unique booking identifier")
    
    # Status tracking
    status: BookingStatus = Field(
        default=BookingStatus.PENDING,
        description="Current booking status"
    )
    
    # Payment
    fee: float = Field(
        default=0.0,
        ge=0,
        description="Consultation fee in USD"
    )
    paymentStatus: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        description="Payment status"
    )
    
    # Payment method and transaction details
    paymentMethod: Optional[Literal["credit_card", "debit_card", "bank_transfer", "wallet", "mobile_money"]] = Field(
        default=None,
        description="Payment method used"
    )
    
    transactionId: Optional[str] = Field(
        default=None,
        description="Payment gateway transaction ID"
    )
    
    # Meeting details
    meetingLink: Optional[str] = Field(
        default=None,
        description="Video call link (for video/call consultations)"
    )
    
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Additional notes about the booking"
    )
    
    lawyerNotes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Lawyer's private notes about the consultation"
    )
    
    # Feedback and ratings
    clientRating: Optional[float] = Field(
        default=None,
        ge=1,
        le=5,
        description="Client's rating of the consultation (1-5 stars)"
    )
    
    clientFeedback: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Client's feedback on the consultation"
    )
    
    lawyerRating: Optional[float] = Field(
        default=None,
        ge=1,
        le=5,
        description="Lawyer's rating of the client (1-5 stars)"
    )
    
    # Timestamps
    createdAt: datetime = Field(default_factory=utc_now, description="Booking creation timestamp")
    updatedAt: datetime = Field(default_factory=utc_now, description="Last update timestamp")
    confirmedAt: Optional[datetime] = Field(default=None, description="When booking was confirmed")
    completedAt: Optional[datetime] = Field(default=None, description="When consultation was completed")
    cancelledAt: Optional[datetime] = Field(default=None, description="When booking was cancelled")
    
    # Cancellation details
    cancellationReason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason for cancellation"
    )
    
    cancellationBy: Optional[Literal["client", "lawyer", "system"]] = Field(
        default=None,
        description="Who cancelled the booking"
    )
    
    # Notifications
    clientNotified: bool = Field(
        default=False,
        description="Whether client has been notified"
    )
    
    lawyerNotified: bool = Field(
        default=False,
        description="Whether lawyer has been notified"
    )
    
    reminderSent: bool = Field(
        default=False,
        description="Whether reminder has been sent"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bookingId": "booking_123456",
                "lawyerId": "lawyer_uid_123",
                "userId": "user_uid_456",
                "consultationType": "video",
                "scheduledAt": "2024-02-15T14:30:00Z",
                "duration": 30,
                "location": "Video call",
                "description": "Consultation regarding employment law",
                "status": "confirmed",
                "fee": 50.0,
                "paymentStatus": "paid",
                "paymentMethod": "credit_card",
                "meetingLink": "https://meet.example.com/booking_123456",
                "createdAt": "2024-02-01T10:00:00Z",
                "updatedAt": "2024-02-01T10:00:00Z",
                "confirmedAt": "2024-02-01T11:30:00Z"
            }
        }
    )


class BookingCreateRequest(BookingBase):
    """
    Request model for creating a new booking
    
    Used in POST /api/bookings endpoint.
    """
    fee: float = Field(
        default=0.0,
        ge=0,
        description="Consultation fee"
    )
    
    paymentMethod: Optional[Literal["credit_card", "debit_card", "bank_transfer", "wallet", "mobile_money"]] = Field(
        default=None,
        description="Payment method"
    )


class BookingUpdateRequest(BaseModel):
    """
    Request model for updating a booking
    
    Used in PUT /api/bookings/{id} endpoint.
    All fields are optional (for rescheduling or status changes).
    """
    scheduledAt: Optional[datetime] = Field(None, description="New scheduled time")
    duration: Optional[int] = Field(None, ge=15, le=240, description="New duration in minutes")
    location: Optional[str] = Field(None, max_length=500, description="New location")
    description: Optional[str] = Field(None, max_length=2000, description="Updated description")
    notes: Optional[str] = Field(None, max_length=2000, description="Updated notes")
    meetingLink: Optional[str] = Field(None, description="Updated meeting link")


class BookingStatusUpdateRequest(BaseModel):
    """
    Request model for updating booking status
    
    Used in PUT /api/bookings/{id}/status endpoint.
    """
    status: BookingStatus = Field(..., description="New booking status")
    cancellationReason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason if cancelling"
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Notes about status change"
    )


class BookingFeedbackRequest(BaseModel):
    """
    Request model for providing feedback on a booking
    
    Used in POST /api/bookings/{id}/feedback endpoint.
    """
    rating: float = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    feedback: str = Field(..., min_length=10, max_length=1000, description="Feedback text")


class BookingResponse(Booking):
    """
    Response model for booking endpoints
    
    This is the public-facing version of the Booking model.
    """
    # Hide sensitive lawyer notes in response
    lawyerNotes: Optional[str] = Field(default=None, exclude=True)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bookingId": "booking_123456",
                "lawyerId": "lawyer_uid_123",
                "userId": "user_uid_456",
                "consultationType": "video",
                "scheduledAt": "2024-02-15T14:30:00Z",
                "duration": 30,
                "status": "confirmed",
                "fee": 50.0,
                "paymentStatus": "paid",
                "createdAt": "2024-02-01T10:00:00Z"
            }
        }
    )


class BookingListResponse(BaseModel):
    """Response model for listing bookings"""
    bookings: list[BookingResponse] = Field(..., description="List of bookings")
    total: int = Field(..., description="Total count of bookings")
    page: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Page size")


class BookingDetailResponse(BookingResponse):
    """
    Detailed response model for a single booking
    
    Includes all booking information and feedback.
    """
    pass


class BookingStats(BaseModel):
    """
    Booking statistics model
    
    Can be stored as a separate document or calculated on-demand.
    """
    totalBookings: int = Field(default=0, description="Total number of bookings")
    completedBookings: int = Field(default=0, description="Completed bookings")
    pendingBookings: int = Field(default=0, description="Pending bookings")
    cancelledBookings: int = Field(default=0, description="Cancelled bookings")
    
    # Financial metrics
    totalRevenue: float = Field(default=0.0, description="Total revenue from bookings")
    paidAmount: float = Field(default=0.0, description="Amount actually paid")
    pendingAmount: float = Field(default=0.0, description="Amount pending")
    
    # Metrics by consultation type
    bookingsByType: dict = Field(default_factory=dict, description="Bookings grouped by type")
    
    # Rating metrics
    averageClientRating: Optional[float] = Field(
        default=None,
        description="Average rating from clients"
    )
    
    averageLawyerRating: Optional[float] = Field(
        default=None,
        description="Average rating from lawyers"
    )
    
    # Time metrics
    averageCompletionTime: Optional[float] = Field(
        default=None,
        description="Average time to complete a booking"
    )
    
    lastUpdatedAt: datetime = Field(default_factory=utc_now, description="Last stats update")


# Helper function to convert Firestore document to Booking model
def firestore_booking_to_model(doc_data: dict, bookingId: str) -> Booking:
    """
    Convert Firestore document data to Booking model
    
    Args:
        doc_data: Dictionary from Firestore document
        bookingId: Booking ID
        
    Returns:
        Booking model instance
    """
    return Booking(
        bookingId=bookingId,
        lawyerId=doc_data.get("lawyerId"),
        userId=doc_data.get("userId"),
        consultationType=doc_data.get("consultationType", "call"),
        scheduledAt=_parse_datetime(doc_data.get("scheduledAt")),
        duration=doc_data.get("duration", 30),
        location=doc_data.get("location"),
        description=doc_data.get("description"),
        caseId=doc_data.get("caseId"),
        tags=doc_data.get("tags", []),
        status=doc_data.get("status", "pending"),
        fee=doc_data.get("fee", 0.0),
        paymentStatus=doc_data.get("paymentStatus", "pending"),
        paymentMethod=doc_data.get("paymentMethod"),
        transactionId=doc_data.get("transactionId"),
        meetingLink=doc_data.get("meetingLink"),
        notes=doc_data.get("notes"),
        lawyerNotes=doc_data.get("lawyerNotes"),
        clientRating=doc_data.get("clientRating"),
        clientFeedback=doc_data.get("clientFeedback"),
        lawyerRating=doc_data.get("lawyerRating"),
        createdAt=_parse_datetime(doc_data.get("createdAt")),
        updatedAt=_parse_datetime(doc_data.get("updatedAt")),
        confirmedAt=_parse_datetime(doc_data.get("confirmedAt")) if doc_data.get("confirmedAt") else None,
        completedAt=_parse_datetime(doc_data.get("completedAt")) if doc_data.get("completedAt") else None,
        cancelledAt=_parse_datetime(doc_data.get("cancelledAt")) if doc_data.get("cancelledAt") else None,
        cancellationReason=doc_data.get("cancellationReason"),
        cancellationBy=doc_data.get("cancellationBy"),
        clientNotified=doc_data.get("clientNotified", False),
        lawyerNotified=doc_data.get("lawyerNotified", False),
        reminderSent=doc_data.get("reminderSent", False)
    )


# Helper function to convert Booking model to Firestore document
def booking_model_to_firestore(booking: Booking) -> dict:
    """
    Convert Booking model to Firestore document format
    
    Args:
        booking: Booking model instance
        
    Returns:
        Dictionary for Firestore storage
    """
    return {
        "lawyerId": booking.lawyerId,
        "userId": booking.userId,
        "consultationType": booking.consultationType.value,
        "scheduledAt": booking.scheduledAt,
        "duration": booking.duration,
        "location": booking.location,
        "description": booking.description,
        "caseId": booking.caseId,
        "tags": booking.tags,
        "status": booking.status.value,
        "fee": booking.fee,
        "paymentStatus": booking.paymentStatus.value,
        "paymentMethod": booking.paymentMethod,
        "transactionId": booking.transactionId,
        "meetingLink": booking.meetingLink,
        "notes": booking.notes,
        "lawyerNotes": booking.lawyerNotes,
        "clientRating": booking.clientRating,
        "clientFeedback": booking.clientFeedback,
        "lawyerRating": booking.lawyerRating,
        "createdAt": booking.createdAt,
        "updatedAt": booking.updatedAt,
        "confirmedAt": booking.confirmedAt,
        "completedAt": booking.completedAt,
        "cancelledAt": booking.cancelledAt,
        "cancellationReason": booking.cancellationReason,
        "cancellationBy": booking.cancellationBy,
        "clientNotified": booking.clientNotified,
        "lawyerNotified": booking.lawyerNotified,
        "reminderSent": booking.reminderSent
    }
