import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta

from app.main import app
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus, ConsultationType
from app.schemas.booking import BookingStatusSchema
from app.dependencies import require_lawyer
from fastapi import status

# Helper for timezone-aware UTC datetime
def utc_now():
    return datetime.now(timezone.utc)

# Mock authenticated lawyer and user
mock_lawyer_user = User(
    uid="lawyer_uid_123",
    email="lawyer@example.com",
    display_name="Lawyer Test",
    role=UserRole.LAWYER,
    created_at=utc_now(),
    updated_at=utc_now(),
)

mock_other_lawyer_user = User(
    uid="lawyer_uid_456",
    email="otherlawyer@example.com",
    display_name="Other Lawyer",
    role=UserRole.LAWYER,
    created_at=utc_now(),
    updated_at=utc_now(),
)

mock_citizen_user = User(
    uid="user_uid_789",
    email="citizen@example.com",
    display_name="Citizen Test",
    role=UserRole.CITIZEN,
    created_at=utc_now(),
    updated_at=utc_now(),
)

# Mock booking data
mock_booking_1 = Booking(
    booking_id="booking_001",
    lawyer_id="lawyer_uid_123",
    user_id="user_uid_789",
    consultation_type=ConsultationType.VIDEO,
    scheduled_at=utc_now() + timedelta(days=1),
    duration=30,
    status=BookingStatus.PENDING,
    fee=50.0,
    payment_status="pending",
    created_at=utc_now(),
    updated_at=utc_now(),
)

mock_booking_2 = Booking(
    booking_id="booking_002",
    lawyer_id="lawyer_uid_123",
    user_id="user_uid_789",
    consultation_type=ConsultationType.CALL,
    scheduled_at=utc_now() + timedelta(days=2),
    duration=60,
    status=BookingStatus.CONFIRMED,
    fee=100.0,
    payment_status="paid",
    created_at=utc_now(),
    updated_at=utc_now(),
    confirmed_at=utc_now() + timedelta(hours=1),
)

mock_booking_3 = Booking(
    booking_id="booking_003",
    lawyer_id="lawyer_uid_123",
    user_id="user_uid_000",
    consultation_type=ConsultationType.MEETING,
    scheduled_at=utc_now() - timedelta(days=5),
    duration=45,
    status=BookingStatus.COMPLETED,
    fee=75.0,
    payment_status="paid",
    created_at=utc_now() - timedelta(days=10),
    updated_at=utc_now() - timedelta(days=5),
    completed_at=utc_now() - timedelta(days=5),
)

mock_booking_4_other_lawyer = Booking(
    booking_id="booking_004",
    lawyer_id="lawyer_uid_456",
    user_id="user_uid_789",
    consultation_type=ConsultationType.CHAT,
    scheduled_at=utc_now() + timedelta(days=3),
    duration=30,
    status=BookingStatus.PENDING,
    fee=50.0,
    payment_status="pending",
    created_at=utc_now(),
    updated_at=utc_now(),
)


@pytest.fixture(autouse=True)
def mock_firebase_service():
    """Mocks the firebase_service for all tests."""
    with patch("app.api.routes.lawyers.firebase_service") as mock_service:
        mock_service.get_lawyer_bookings = AsyncMock(return_value=[])
        mock_service.get_booking_by_id = AsyncMock(return_value=None)
        mock_service.update_booking_status = AsyncMock(return_value=None)
        yield mock_service

@pytest.fixture(autouse=True)
def mock_require_lawyer():
    """Mocks the require_lawyer dependency to return our mock lawyer user."""
    async def override_dep():
        return mock_lawyer_user
    app.dependency_overrides[require_lawyer] = override_dep
    yield override_dep
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_lawyer_bookings_success(mock_firebase_service, mock_require_lawyer):
    """Test retrieving a lawyer's bookings successfully."""
    mock_firebase_service.get_lawyer_bookings.return_value = [mock_booking_1, mock_booking_2]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/lawyers/{mock_lawyer_user.uid}/bookings")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 2
    assert len(data["bookings"]) == 2
    assert data["bookings"][0]["bookingId"] == mock_booking_1.booking_id
    assert data["bookings"][1]["bookingId"] == mock_booking_2.booking_id
    mock_firebase_service.get_lawyer_bookings.assert_called_once_with(
        lawyer_uid=mock_lawyer_user.uid, status=None, limit=10, offset=0
    )


@pytest.mark.asyncio
async def test_get_lawyer_bookings_with_status_filter(mock_firebase_service, mock_require_lawyer):
    """Test retrieving a lawyer's bookings filtered by status."""
    mock_firebase_service.get_lawyer_bookings.return_value = [mock_booking_1]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/lawyers/{mock_lawyer_user.uid}/bookings?status=pending")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["bookings"][0]["bookingId"] == mock_booking_1.booking_id
    mock_firebase_service.get_lawyer_bookings.assert_called_once_with(
        lawyer_uid=mock_lawyer_user.uid, status=BookingStatus.PENDING, limit=10, offset=0
    )


@pytest.mark.asyncio
async def test_get_lawyer_bookings_unauthorized_lawyer_id(mock_firebase_service, mock_require_lawyer):
    """Test retrieving bookings for a lawyer not matching the authenticated one."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/lawyers/{mock_other_lawyer_user.uid}/bookings")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not authorized" in response.json()["detail"].lower()
    mock_firebase_service.get_lawyer_bookings.assert_not_called()


@pytest.mark.asyncio
async def test_get_lawyer_booking_detail_success(mock_firebase_service, mock_require_lawyer):
    """Test retrieving a single booking's details successfully."""
    mock_firebase_service.get_booking_by_id.return_value = mock_booking_1

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/lawyers/bookings/{mock_booking_1.booking_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["bookingId"] == mock_booking_1.booking_id
    mock_firebase_service.get_booking_by_id.assert_called_once_with(mock_booking_1.booking_id)


@pytest.mark.asyncio
async def test_get_lawyer_booking_detail_not_found(mock_firebase_service, mock_require_lawyer):
    """Test retrieving a booking that does not exist."""
    mock_firebase_service.get_booking_by_id.return_value = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/lawyers/bookings/non_existent_booking")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
    mock_firebase_service.get_booking_by_id.assert_called_once_with("non_existent_booking")


@pytest.mark.asyncio
async def test_get_lawyer_booking_detail_unauthorized(mock_firebase_service, mock_require_lawyer):
    """Test retrieving a booking belonging to another lawyer."""
    mock_firebase_service.get_booking_by_id.return_value = mock_booking_4_other_lawyer

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/lawyers/bookings/{mock_booking_4_other_lawyer.booking_id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not authorized to view" in response.json()["detail"].lower()
    mock_firebase_service.get_booking_by_id.assert_called_once_with(mock_booking_4_other_lawyer.booking_id)


@pytest.mark.asyncio
async def test_update_lawyer_booking_status_confirm_success(mock_firebase_service, mock_require_lawyer):
    """Test confirming a booking successfully."""
    mock_firebase_service.get_booking_by_id.return_value = mock_booking_1
    updated_booking = mock_booking_1.model_copy(update={"status": BookingStatus.CONFIRMED, "confirmed_at": utc_now()})
    mock_firebase_service.update_booking_status.return_value = updated_booking

    status_data = BookingStatusSchema(status=BookingStatus.CONFIRMED).model_dump(by_alias=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/lawyers/bookings/{mock_booking_1.booking_id}/status", json=status_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["bookingId"] == mock_booking_1.booking_id
    assert data["status"] == BookingStatus.CONFIRMED.value
    mock_firebase_service.get_booking_by_id.assert_called_once_with(mock_booking_1.booking_id)
    mock_firebase_service.update_booking_status.assert_called_once()
    args, kwargs = mock_firebase_service.update_booking_status.call_args
    assert kwargs["booking_id"] == mock_booking_1.booking_id
    assert kwargs["new_status"] == BookingStatus.CONFIRMED


@pytest.mark.asyncio
async def test_update_lawyer_booking_status_cancel_success(mock_firebase_service, mock_require_lawyer):
    """Test cancelling a booking successfully."""
    mock_firebase_service.get_booking_by_id.return_value = mock_booking_1
    updated_booking = mock_booking_1.model_copy(update={"status": BookingStatus.CANCELLED, "cancelled_at": utc_now(), "cancellation_reason": "Lawyer unavailable"})
    mock_firebase_service.update_booking_status.return_value = updated_booking

    status_data = BookingStatusSchema(status=BookingStatus.CANCELLED, cancellation_reason="Lawyer unavailable", notes="Lawyer note").model_dump(by_alias=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/lawyers/bookings/{mock_booking_1.booking_id}/status", json=status_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["bookingId"] == mock_booking_1.booking_id
    assert data["status"] == BookingStatus.CANCELLED.value
    assert data["cancellationReason"] == "Lawyer unavailable"
    mock_firebase_service.update_booking_status.assert_called_once()
    args, kwargs = mock_firebase_service.update_booking_status.call_args
    assert kwargs["booking_id"] == mock_booking_1.booking_id
    assert kwargs["new_status"] == BookingStatus.CANCELLED
    assert kwargs["cancellation_reason"] == "Lawyer unavailable"
    assert kwargs["lawyer_notes"] == "Lawyer note"


@pytest.mark.asyncio
async def test_update_lawyer_booking_status_not_found(mock_firebase_service, mock_require_lawyer):
    """Test updating status for a booking that does not exist."""
    mock_firebase_service.get_booking_by_id.return_value = None

    status_data = BookingStatusSchema(status=BookingStatus.CONFIRMED).model_dump(by_alias=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/lawyers/bookings/non_existent_booking/status", json=status_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
    mock_firebase_service.get_booking_by_id.assert_called_once_with("non_existent_booking")
    mock_firebase_service.update_booking_status.assert_not_called()


@pytest.mark.asyncio
async def test_update_lawyer_booking_status_unauthorized(mock_firebase_service, mock_require_lawyer):
    """Test updating status for a booking belonging to another lawyer."""
    mock_firebase_service.get_booking_by_id.return_value = mock_booking_4_other_lawyer

    status_data = BookingStatusSchema(status=BookingStatus.CONFIRMED).model_dump(by_alias=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/lawyers/bookings/{mock_booking_4_other_lawyer.booking_id}/status", json=status_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not authorized to update" in response.json()["detail"].lower()
    mock_firebase_service.get_booking_by_id.assert_called_once_with(mock_booking_4_other_lawyer.booking_id)
    mock_firebase_service.update_booking_status.assert_not_called()


@pytest.mark.asyncio
async def test_update_lawyer_booking_status_firebase_failure(mock_firebase_service, mock_require_lawyer):
    """Test Firebase service failure during status update."""
    mock_firebase_service.get_booking_by_id.return_value = mock_booking_1
    mock_firebase_service.update_booking_status.return_value = None  # Simulate update failure

    status_data = BookingStatusSchema(status=BookingStatus.CONFIRMED).model_dump(by_alias=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/lawyers/bookings/{mock_booking_1.booking_id}/status", json=status_data)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "failed to update" in response.json()["detail"].lower()
    mock_firebase_service.get_booking_by_id.assert_called_once_with(mock_booking_1.booking_id)
    mock_firebase_service.update_booking_status.assert_called_once()
