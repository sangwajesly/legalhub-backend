"""
Booking request/response schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from app.models.booking import (
    BookingStatus,
    PaymentStatus,
    ConsultationType,
)


class BookingCreateSchema(BaseModel):
    """Schema for creating a new booking"""

    lawyer_id: str = Field(..., description="Lawyer's UID", alias="lawyerId")
    consultation_type: ConsultationType = Field(
        default=ConsultationType.CALL, description="Type of consultation", alias="consultationType"
    )
    scheduled_at: datetime = Field(
        ..., description="When to schedule the consultation", alias="scheduledAt")
    duration: int = Field(default=30, ge=15, le=240,
                          description="Duration in minutes")
    location: Optional[str] = Field(
        None, max_length=500, description="Meeting location or contact"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Consultation topic"
    )
    case_id: Optional[str] = Field(
        None, description="Related case ID if any", alias="caseId")
    tags: list[str] = Field(default_factory=list,
                            max_length=10, description="Tags")
    fee: float = Field(default=0.0, ge=0, description="Consultation fee")
    payment_method: Optional[
        Literal["credit_card", "debit_card", "bank_transfer", "wallet"]
    ] = Field(None, description="Payment method", alias="paymentMethod")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "lawyerId": "lawyer_123",
                "consultationType": "video",
                "scheduledAt": "2024-02-15T14:30:00Z",
                "duration": 30,
                "location": "Video call via Zoom",
                "description": "Discuss employment contract review",
                "fee": 50.0,
                "paymentMethod": "credit_card",
            }
        }
    )


class BookingUpdateSchema(BaseModel):
    """Schema for updating a booking"""

    scheduled_at: Optional[datetime] = Field(
        None, description="New scheduled time", alias="scheduledAt")
    duration: Optional[int] = Field(
        None, ge=15, le=240, description="New duration")
    location: Optional[str] = Field(
        None, max_length=500, description="New location")
    description: Optional[str] = Field(
        None, max_length=2000, description="Updated description"
    )
    notes: Optional[str] = Field(
        None, max_length=2000, description="Updated notes")
    meeting_link: Optional[str] = Field(
        None, description="Updated meeting link", alias="meetingLink")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "scheduledAt": "2024-02-16T15:00:00Z",
                "duration": 45,
                "notes": "Rescheduled due to conflict",
            }
        }
    )


class BookingStatusSchema(BaseModel):
    """Schema for updating booking status"""

    status: BookingStatus = Field(..., description="New status")
    cancellation_reason: Optional[str] = Field(
        None, max_length=500, description="Reason if cancelling", alias="cancellationReason"
    )
    notes: Optional[str] = Field(None, max_length=2000, description="Notes")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {"status": "confirmed", "notes": "Confirmed by lawyer"}
        }
    )


class BookingFeedbackSchema(BaseModel):
    """Schema for providing feedback"""

    rating: float = Field(..., ge=1, le=5, description="Rating 1-5")
    feedback: str = Field(
        ..., min_length=10, max_length=1000, description="Feedback text"
    )

    model_config = ConfigDict(populate_by_name=True)


class BookingResponse(BaseModel):
    """Response schema for a booking"""

    booking_id: str = Field(..., alias="bookingId")
    lawyer_id: str = Field(..., alias="lawyerId")
    user_id: str = Field(..., alias="userId")
    consultation_type: str = Field(..., alias="consultationType")
    scheduled_at: datetime = Field(..., alias="scheduledAt")
    duration: int
    status: str
    fee: float
    payment_status: str = Field(..., alias="paymentStatus")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    client_rating: Optional[float] = Field(None, alias="clientRating")
    client_feedback: Optional[str] = Field(None, alias="clientFeedback")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "bookingId": "booking_123",
                "lawyerId": "lawyer_123",
                "userId": "user_456",
                "consultationType": "video",
                "scheduledAt": "2024-02-15T14:30:00Z",
                "duration": 30,
                "status": "confirmed",
                "fee": 50.0,
                "paymentStatus": "paid",
                "createdAt": "2024-02-01T10:00:00Z",
                "updatedAt": "2024-02-01T10:00:00Z",
            }
        }
    )


class BookingListSchema(BaseModel):
    """Response schema for listing bookings"""

    bookings: list[BookingResponse]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "bookings": [
                    {
                        "bookingId": "booking_123",
                        "lawyerId": "lawyer_123",
                        "userId": "user_456",
                        "consultationType": "video",
                        "scheduledAt": "2024-02-15T14:30:00Z",
                        "duration": 30,
                        "status": "confirmed",
                        "fee": 50.0,
                        "paymentStatus": "paid",
                        "createdAt": "2024-02-01T10:00:00Z",
                        "updatedAt": "2024-02-01T10:00:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "pageSize": 20,
            }
        }
    )


class BookingDetailSchema(BookingResponse):
    """Detailed response schema for a single booking"""

    location: Optional[str] = None
    description: Optional[str] = None
    meeting_link: Optional[str] = Field(None, alias="meetingLink")
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = Field(
        None, alias="cancellationReason")
    lawyer_rating: Optional[float] = Field(None, alias="lawyerRating")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
