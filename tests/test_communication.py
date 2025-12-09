import sys
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Mock heavy deps
faiss_mock = MagicMock()
faiss_mock.__spec__ = MagicMock()
sys.modules["faiss"] = faiss_mock
st_mock = MagicMock()
st_mock.__spec__ = MagicMock()
sys.modules["sentence_transformers"] = st_mock

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user
from app.models.communication import DirectMessage

client = TestClient(app)

@pytest.fixture
def mock_firebase_service():
    with patch("app.api.routes.communication.firebase_service") as mock:
        yield mock

@pytest.fixture
def mock_booking_service():
    with patch("app.api.routes.bookings.firebase_service") as mock:
        yield mock

def test_send_message(mock_firebase_service):
    """Test sending a direct message"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "sender1", "role": "user"}
    
    # Mock add_direct_message to return the input (or mostly)
    async def mock_add(msg):
        msg.id = "msg123"
        return msg
    mock_firebase_service.add_direct_message = AsyncMock(side_effect=mock_add)
    
    payload = {
        "receiverId": "receiver1",
        "content": "Hello Lawyer!",
        "bookingId": "bk1"
    }
    
    response = client.post("/api/communication/messages", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["senderId"] == "sender1"
    assert data["receiverId"] == "receiver1"
    assert data["content"] == "Hello Lawyer!"
    assert data["bookingId"] == "bk1"
    assert "timestamp" in data
    
    app.dependency_overrides = {}

def test_get_conversation(mock_firebase_service):
    """Test retrieving conversation"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user1", "role": "user"}
    
    mock_msgs = [
        DirectMessage(senderId="user1", receiverId="user2", content="Hi", timestamp=datetime.now(), id="m1"),
        DirectMessage(senderId="user2", receiverId="user1", content="Hello", timestamp=datetime.now(), id="m2")
    ]
    mock_firebase_service.get_direct_messages = AsyncMock(return_value=mock_msgs)
    
    response = client.get("/api/communication/messages/user2")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "Hi"
    assert data[1]["content"] == "Hello"
    
    app.dependency_overrides = {}

def test_join_call_success(mock_booking_service):
    """Test joining a valid call as a participant"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "client1", "role": "user"}
    
    # Mock booking existence
    mock_booking_service.get_document = AsyncMock(return_value={
        "userId": "client1",
        "lawyerId": "lawyer1",
        "status": "confirmed",
        "scheduledAt": datetime.now().isoformat(),
        "durationMinutes": 30,
        "fee": 100
    })
    
    response = client.post("/api/bookings/bk100/join_call")
    
    assert response.status_code == 200
    data = response.json()
    assert "meet.jit.si" in data["roomUrl"]
    assert "bk100" in data["roomName"]
    
    app.dependency_overrides = {}

def test_join_call_forbidden(mock_booking_service):
    """Test joining a call as non-participant"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "stranger1", "role": "user"}
    
    mock_booking_service.get_document = AsyncMock(return_value={
        "userId": "client1",
        "lawyerId": "lawyer1"
    })
    
    response = client.post("/api/bookings/bk100/join_call")
    
    assert response.status_code == 403
    
    app.dependency_overrides = {}
