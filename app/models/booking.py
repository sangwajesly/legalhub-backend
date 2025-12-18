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

    lawyer_id: str = Field(...,
                           description="Firebase UID of the lawyer", alias="lawyerId")
    user_id: str = Field(...,
                         description="Firebase UID of the client", alias="userId")
    consultation_type: ConsultationType = Field(
        default=ConsultationType.CALL, description="Type of consultation", alias="consultationType"
    )

    # Scheduling
    scheduled_at: datetime = Field(
        ..., description="Scheduled consultation timestamp", alias="scheduledAt")
    duration: int = Field(
        default=30, ge=15, le=240, description="Consultation duration in minutes"
    )

    # Location/Contact info
    location: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Meeting location (for in-person) or contact details",
    )

    # Description and case details
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Brief description of the consultation topic",
    )

    case_id: Optional[str] = Field(
        default=None, description="Reference to a case if this booking is related", alias="caseId"
    )

    # Tags/categories
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Tags for consultation categorization",
    )

    model_config = ConfigDict(populate_by_name=True)


class Booking(BookingBase):
    """
    Complete Booking model representing a lawyer consultation booking in Firestore

    Collection: bookings/
    Document ID: bookingId (auto-generated)
    """

    booking_id: str = Field(...,
                            description="Unique booking identifier", alias="bookingId")

    # Status tracking
    status: BookingStatus = Field(
        default=BookingStatus.PENDING, description="Current booking status"
    )

    # Payment
    fee: float = Field(default=0.0, ge=0,
                       description="Consultation fee in USD")
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, description="Payment status", alias="paymentStatus"
    )

    # Payment method and transaction details
    payment_method: Optional[
        Literal["credit_card", "debit_card",
                "bank_transfer", "wallet", "mobile_money"]
    ] = Field(default=None, description="Payment method used", alias="paymentMethod")

    transaction_id: Optional[str] = Field(
        default=None, description="Payment gateway transaction ID", alias="transactionId"
    )

    # Meeting details
    meeting_link: Optional[str] = Field(
        default=None, description="Video call link (for video/call consultations)", alias="meetingLink"
    )

    notes: Optional[str] = Field(
        default=None, max_length=2000, description="Additional notes about the booking"
    )

    lawyer_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Lawyer's private notes about the consultation",
        alias="lawyerNotes"
    )

    # Feedback and ratings
    client_rating: Optional[float] = Field(
        default=None,
        ge=1,
        le=5,
        description="Client's rating of the consultation (1-5 stars)",
        alias="clientRating"
    )

    client_feedback: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Client's feedback on the consultation",
        alias="clientFeedback"
    )

    lawyer_rating: Optional[float] = Field(
        default=None,
        ge=1,
        le=5,
        description="Lawyer's rating of the client (1-5 stars)",
        alias="lawyerRating"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=utc_now, description="Booking creation timestamp", alias="createdAt"
    )
    updated_at: datetime = Field(
        default_factory=utc_now, description="Last update timestamp", alias="updatedAt"
    )
    confirmed_at: Optional[datetime] = Field(
        default=None, description="When booking was confirmed", alias="confirmedAt"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When consultation was completed", alias="completedAt"
    )
    cancelled_at: Optional[datetime] = Field(
        default=None, description="When booking was cancelled", alias="cancelledAt"
    )

    # Cancellation details
    cancellation_reason: Optional[str] = Field(
        default=None, max_length=500, description="Reason for cancellation", alias="cancellationReason"
    )

    cancellation_by: Optional[Literal["client", "lawyer", "system"]] = Field(
        default=None, description="Who cancelled the booking", alias="cancellationBy"
    )

    # Notifications
    client_notified: bool = Field(
        default=False, description="Whether client has been notified", alias="clientNotified"
    )

    lawyer_notified: bool = Field(
        default=False, description="Whether lawyer has been notified", alias="lawyerNotified"
    )

    reminder_sent: bool = Field(
        default=False, description="Whether reminder has been sent", alias="reminderSent"
    )

    model_config = ConfigDict(
        populate_by_name=True,
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
                "confirmedAt": "2024-02-01T11:30:00Z",
            }
        }
    )


class BookingCreateRequest(BookingBase):
    """
    Request model for creating a new booking

    Used in POST /api/bookings endpoint.
    """

    fee: float = Field(default=0.0, ge=0, description="Consultation fee")

    payment_method: Optional[
        Literal["credit_card", "debit_card",
                "bank_transfer", "wallet", "mobile_money"]
    ] = Field(default=None, description="Payment method", alias="paymentMethod")


class BookingUpdateRequest(BaseModel):
    """
    Request model for updating a booking

    Used in PUT /api/bookings/{id} endpoint.
    All fields are optional (for rescheduling or status changes).
    """

    scheduled_at: Optional[datetime] = Field(
        None, description="New scheduled time", alias="scheduledAt")
    duration: Optional[int] = Field(
        None, ge=15, le=240, description="New duration in minutes"
    )
    location: Optional[str] = Field(
        None, max_length=500, description="New location")
    description: Optional[str] = Field(
        None, max_length=2000, description="Updated description"
    )
    notes: Optional[str] = Field(
        None, max_length=2000, description="Updated notes")
    meeting_link: Optional[str] = Field(
        None, description="Updated meeting link", alias="meetingLink")

    model_config = ConfigDict(populate_by_name=True)


class BookingStatusUpdateRequest(BaseModel):
    """
    Request model for updating booking status

    Used in PUT /api/bookings/{id}/status endpoint.
    """

    status: BookingStatus = Field(..., description="New booking status")
    cancellation_reason: Optional[str] = Field(
        None, max_length=500, description="Reason if cancelling", alias="cancellationReason"
    )
    notes: Optional[str] = Field(
        None, max_length=2000, description="Notes about status change"
    )

    model_config = ConfigDict(populate_by_name=True)


class BookingFeedbackRequest(BaseModel):
    """
    Request model for providing feedback on a booking

    Used in POST /api/bookings/{id}/feedback endpoint.
    """

    rating: float = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    feedback: str = Field(
        ..., min_length=10, max_length=1000, description="Feedback text"
    )


class BookingResponse(Booking):
    """
    Response model for booking endpoints

    This is the public-facing version of the Booking model.
    """

    # Hide sensitive lawyer notes in response
    lawyer_notes: Optional[str] = Field(
        default=None, exclude=True, alias="lawyerNotes")

    model_config = ConfigDict(
        populate_by_name=True,
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
                "createdAt": "2024-02-01T10:00:00Z",
            }
        }
    )


class BookingListResponse(BaseModel):
    """Response model for listing bookings"""

    bookings: list[BookingResponse] = Field(...,
                                            description="List of bookings")
    total: int = Field(..., description="Total count of bookings")
    page: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Page size", alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


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

    total_bookings: int = Field(
        default=0, description="Total number of bookings", alias="totalBookings")
    completed_bookings: int = Field(
        default=0, description="Completed bookings", alias="completedBookings")
    pending_bookings: int = Field(
        default=0, description="Pending bookings", alias="pendingBookings")
    cancelled_bookings: int = Field(
        default=0, description="Cancelled bookings", alias="cancelledBookings")

    # Financial metrics
    total_revenue: float = Field(
        default=0.0, description="Total revenue from bookings", alias="totalRevenue")
    paid_amount: float = Field(
        default=0.0, description="Amount actually paid", alias="paidAmount")
    pending_amount: float = Field(
        default=0.0, description="Amount pending", alias="pendingAmount")

    # Metrics by consultation type
    bookings_by_type: dict = Field(
        default_factory=dict, description="Bookings grouped by type", alias="bookingsByType"
    )

    # Rating metrics
    average_client_rating: Optional[float] = Field(
        default=None, description="Average rating from clients", alias="averageClientRating"
    )

    average_lawyer_rating: Optional[float] = Field(
        default=None, description="Average rating from lawyers", alias="averageLawyerRating"
    )

    # Time metrics
    average_completion_time: Optional[float] = Field(
        default=None, description="Average time to complete a booking", alias="averageCompletionTime"
    )

    last_updated_at: datetime = Field(
        default_factory=utc_now, description="Last stats update", alias="lastUpdatedAt"
    )

    model_config = ConfigDict(populate_by_name=True)


# Helper function to convert Firestore document to Booking model
def firestore_booking_to_model(doc_data: dict, booking_id: str) -> Booking:
    return Booking.model_validate({**doc_data, "bookingId": booking_id})


# Helper function to convert Booking model to Firestore document
def booking_model_to_firestore(booking: Booking) -> dict:
    data = booking.model_dump(by_alias=True)
    data.pop("bookingId", None)
    return data
