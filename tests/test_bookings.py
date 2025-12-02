"""
Tests for booking endpoints

Tests cover:
- Creating bookings
- Getting and listing bookings
- Updating and rescheduling bookings
- Changing booking status
- Providing feedback/ratings
- Booking statistics
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC, timedelta

from app.main import app
from app.services import firebase_service


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {"uid": "test_user_123", "email": "client@example.com", "is_admin": False}


@pytest.fixture(autouse=True)
def mock_firebase():
    """Mock Firebase service for all tests"""
    # In-memory store for testing
    store = {}

    async def get_doc(path):
        return store.get(path)

    async def set_doc(path, data):
        store[path] = data

    async def update_doc(path, data):
        if path in store:
            store[path].update(data)
        else:
            store[path] = data

    async def query_docs(collection, filters=None, limit=100, offset=0):
        # Filter documents from store
        docs = []
        for path, data in store.items():
            if path.startswith(f"{collection}/"):
                doc_id = path.split("/")[-1]
                match = True
                if filters:
                    for key, value in filters.items():
                        if data.get(key) != value:
                            match = False
                            break
                if match:
                    docs.append((doc_id, data))

        total = len(docs)
        paginated = docs[offset : offset + limit]
        return paginated, total

    async def delete_doc(path):
        if path in store:
            del store[path]

    # Patch the instance methods
    firebase_service.get_document = get_doc
    firebase_service.set_document = set_doc
    firebase_service.update_document = update_doc
    firebase_service.query_collection = query_docs
    firebase_service.delete_document = delete_doc

    yield {"store": store}

    # Clean up
    for attr in [
        "get_document",
        "set_document",
        "update_document",
        "query_collection",
        "delete_document",
    ]:
        if hasattr(firebase_service, attr):
            delattr(firebase_service, attr)


@pytest.fixture
def mock_auth(mock_current_user):
    """Mock authentication dependency"""
    from app.dependencies import get_current_user

    def override_get_current_user():
        return mock_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


def test_create_booking_unauthenticated(client):
    """Test creating a booking without authentication"""
    scheduled_time = (datetime.now(UTC) + timedelta(days=7)).isoformat()

    response = client.post(
        "/api/bookings/",
        json={
            "lawyerId": "lawyer_123",
            "consultationType": "video",
            "scheduledAt": scheduled_time,
            "duration": 30,
            "fee": 50.0,
        },
    )

    assert response.status_code == 403


def test_create_booking_lawyer_not_found(
    client, mock_current_user, mock_auth, mock_firebase
):
    """Test creating a booking with non-existent lawyer"""
    scheduled_time = (datetime.now(UTC) + timedelta(days=7)).isoformat()

    response = client.post(
        "/api/bookings/",
        json={
            "lawyerId": "nonexistent_lawyer",
            "consultationType": "video",
            "scheduledAt": scheduled_time,
            "duration": 30,
            "fee": 50.0,
        },
    )

    assert response.status_code == 404
    assert "Lawyer not found" in response.json()["detail"]


def test_create_booking_success(client, mock_current_user, mock_auth, mock_firebase):
    """Test creating a booking successfully"""
    # Mock lawyer exists
    mock_firebase["store"]["lawyers/lawyer_123"] = {
        "uid": "lawyer_123",
        "name": "John Lawyer",
        "specialization": "employment",
    }

    scheduled_time = (datetime.now(UTC) + timedelta(days=7)).isoformat()

    response = client.post(
        "/api/bookings/",
        json={
            "lawyerId": "lawyer_123",
            "consultationType": "video",
            "scheduledAt": scheduled_time,
            "duration": 30,
            "location": "Video call",
            "description": "Employment law consultation",
            "fee": 50.0,
            "paymentMethod": "credit_card",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["lawyerId"] == "lawyer_123"
    assert data["userId"] == "test_user_123"
    assert data["status"] == "pending"
    assert data["paymentStatus"] == "pending"
    assert data["fee"] == 50.0


def test_get_booking_not_found(client, mock_current_user, mock_auth):
    """Test retrieving non-existent booking"""
    response = client.get("/api/bookings/nonexistent")

    assert response.status_code == 404


def test_get_booking_success(client, mock_current_user, mock_auth, mock_firebase):
    """Test retrieving a booking"""
    # Create a booking in store
    booking_data = {
        "bookingId": "booking_123",
        "lawyerId": "lawyer_123",
        "userId": "test_user_123",
        "consultationType": "video",
        "scheduledAt": datetime.now(UTC).isoformat(),
        "duration": 30,
        "status": "confirmed",
        "paymentStatus": "paid",
        "fee": 50.0,
        "createdAt": datetime.now(UTC).isoformat(),
    }
    mock_firebase["store"]["bookings/booking_123"] = booking_data

    response = client.get("/api/bookings/booking_123")

    assert response.status_code == 200
    data = response.json()
    assert data["bookingId"] == "booking_123"
    assert data["status"] == "confirmed"


def test_list_user_bookings(client, mock_current_user, mock_auth, mock_firebase):
    """Test listing bookings for current user"""
    # Create bookings in store
    for i in range(3):
        mock_firebase["store"][f"bookings/booking_{i}"] = {
            "bookingId": f"booking_{i}",
            "lawyerId": f"lawyer_{i}",
            "userId": "test_user_123",
            "status": "confirmed",
            "fee": 50.0,
        }

    response = client.get("/api/bookings/my")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["bookings"]) == 3


def test_update_booking(client, mock_current_user, mock_auth, mock_firebase):
    """Test updating a booking"""
    # Create a booking
    mock_firebase["store"]["bookings/booking_123"] = {
        "bookingId": "booking_123",
        "lawyerId": "lawyer_123",
        "userId": "test_user_123",
        "scheduledAt": datetime.now(UTC).isoformat(),
        "duration": 30,
        "notes": "Original notes",
    }

    new_time = (datetime.now(UTC) + timedelta(days=8)).isoformat()

    response = client.put(
        "/api/bookings/booking_123",
        json={"scheduledAt": new_time, "duration": 45, "notes": "Updated notes"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["duration"] == 45


def test_update_booking_status(client, mock_current_user, mock_auth, mock_firebase):
    """Test updating booking status"""
    # Create a booking assigned to current user
    mock_firebase["store"]["bookings/booking_123"] = {
        "bookingId": "booking_123",
        "lawyerId": "test_user_123",
        "userId": "other_user",
        "status": "pending",
        "createdAt": datetime.now(UTC).isoformat(),
    }

    response = client.put(
        "/api/bookings/booking_123/status",
        json={"status": "confirmed", "notes": "Confirmed by lawyer"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


def test_cancel_booking(client, mock_current_user, mock_auth, mock_firebase):
    """Test cancelling a booking"""
    # Create a booking
    mock_firebase["store"]["bookings/booking_123"] = {
        "bookingId": "booking_123",
        "lawyerId": "lawyer_123",
        "userId": "test_user_123",
        "status": "confirmed",
        "createdAt": datetime.now(UTC).isoformat(),
    }

    response = client.put(
        "/api/bookings/booking_123/cancel", json={"reason": "Schedule conflict"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


def test_provide_feedback(client, mock_current_user, mock_auth, mock_firebase):
    """Test providing feedback on a booking"""
    # Create a completed booking
    mock_firebase["store"]["bookings/booking_123"] = {
        "bookingId": "booking_123",
        "lawyerId": "lawyer_123",
        "userId": "test_user_123",
        "status": "completed",
    }

    response = client.post(
        "/api/bookings/booking_123/feedback",
        json={"rating": 5, "feedback": "Excellent consultation, very helpful!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["clientRating"] == 5


def test_booking_stats_unauthorized(client, mock_current_user, mock_auth):
    """Test getting stats without admin permission"""
    response = client.get("/api/bookings/stats/overview")

    assert response.status_code == 403
    assert "Admin" in response.json()["detail"]


def test_booking_stats_admin(client, mock_auth, mock_firebase):
    """Test getting booking statistics as admin"""
    # Override to admin user
    admin_user = {"uid": "admin_123", "email": "admin@example.com", "is_admin": True}
    from app.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: admin_user

    # Create bookings in store
    mock_firebase["store"]["bookings/booking_1"] = {
        "status": "completed",
        "paymentStatus": "paid",
        "fee": 50.0,
        "clientRating": 5,
    }
    mock_firebase["store"]["bookings/booking_2"] = {
        "status": "cancelled",
        "paymentStatus": "refunded",
        "fee": 30.0,
    }

    response = client.get("/api/bookings/stats/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["totalBookings"] == 2
    assert data["completedBookings"] == 1
    assert data["cancelledBookings"] == 1

    app.dependency_overrides.clear()
