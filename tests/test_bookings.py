import sys
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, UTC

# 1. Mock heavy dependencies BEFORE any app imports
faiss_mock = MagicMock()
faiss_mock.__spec__ = MagicMock()
sys.modules["faiss"] = faiss_mock
st_mock = MagicMock()
st_mock.__spec__ = MagicMock()
sys.modules["sentence_transformers"] = st_mock

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import UserRole
from app.dependencies import get_current_user
from app.models.booking import BookingStatus

client = TestClient(app)

@pytest.fixture
def mock_firebase_service():
    with patch("app.api.routes.bookings.firebase_service") as mock:
        yield mock

@pytest.fixture
def mock_notification_service():
    with patch("app.api.routes.bookings.notification_service") as mock:
        yield mock

# --- Tests ---

def test_list_bookings_rbac_lawyer(mock_firebase_service):
    """Lawyers can list their assigned bookings"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "l1", "role": UserRole.LAWYER}
    
    # Mock return
    mock_firebase_service.query_collection = AsyncMock(return_value=([], 0))
    
    client.get("/api/bookings")
    
    # Verify filters contained lawyerId=l1
    args = mock_firebase_service.query_collection.call_args
    assert args.kwargs["filters"]["lawyerId"] == "l1"
    assert "userId" not in args.kwargs["filters"]
    
    app.dependency_overrides = {}

def test_list_bookings_rbac_client(mock_firebase_service):
    """Clients can list their own bookings"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": UserRole.USER}
    
    mock_firebase_service.query_collection = AsyncMock(return_value=([], 0))
    
    client.get("/api/bookings")
    
    args = mock_firebase_service.query_collection.call_args
    assert args.kwargs["filters"]["userId"] == "u1"
    assert "lawyerId" not in args.kwargs["filters"]
    
    app.dependency_overrides = {}

def test_create_booking_future_check(mock_firebase_service):
    """Booking for past time should fail"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": UserRole.USER}
    mock_firebase_service.get_document = AsyncMock(return_value={"uid": "l1"}) # Lawyer exists
    
    past_date = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    
    payload = {
        "lawyerId": "l1",
        "scheduledAt": past_date,
        "duration": 30
    }
    
    response = client.post("/api/bookings/", json=payload)
    assert response.status_code == 400
    assert "at least 15 minutes" in response.json()["detail"]
    app.dependency_overrides = {}

def test_create_booking_conflict(mock_firebase_service):
    """Booking overlapping with existing confirmed booking should fail"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": UserRole.USER}
    mock_firebase_service.get_document = AsyncMock(return_value={"uid": "l1"})
    mock_firebase_service.set_document = AsyncMock()

    # Existing booking: Now + 1 hour, duration 30 mins
    base_time = datetime.now(UTC) + timedelta(days=1, hours=10) # Tomorrow 10am
    
    existing_booking = {
        "bookingId": "b1",
        "lawyerId": "l1",
        "userId": "u2",
        "status": "confirmed",
        "scheduledAt": base_time.isoformat(),
        "duration": 30,
        "createdAt": base_time.isoformat(),
        "updatedAt": base_time.isoformat()
    }
    
    # Return existing booking when querying
    mock_firebase_service.query_collection = AsyncMock(return_value=([( "b1", existing_booking )], 1))

    # Try to book overlapping slot (Tomorrow 10:15am, duration 30 mins) -> overlaps 10:15-10:30
    new_start = base_time + timedelta(minutes=15)
    
    payload = {
        "lawyerId": "l1",
        "scheduledAt": new_start.isoformat(),
        "duration": 30
    }
    
    response = client.post("/api/bookings/", json=payload)
    assert response.status_code == 409
    assert "already booked" in response.json()["detail"]
    app.dependency_overrides = {}

def test_create_booking_success(mock_firebase_service):
    """Booking non-overlapping slot should succeed"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": UserRole.USER}
    mock_firebase_service.get_document = AsyncMock(return_value={"uid": "l1"})
    mock_firebase_service.set_document = AsyncMock()
    mock_firebase_service.query_collection = AsyncMock(return_value=([], 0)) # No conflicts

    future_time = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    
    payload = {
        "lawyerId": "l1",
        "scheduledAt": future_time,
        "duration": 30
    }
    
    response = client.post("/api/bookings/", json=payload)
    assert response.status_code == 201
    app.dependency_overrides = {}
