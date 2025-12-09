import sys
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Mock heavy dependencies
faiss_mock = MagicMock()
faiss_mock.__spec__ = MagicMock()
sys.modules["faiss"] = faiss_mock
st_mock = MagicMock()
st_mock.__spec__ = MagicMock()
sys.modules["sentence_transformers"] = st_mock

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User, UserRole

client = TestClient(app)

@pytest.fixture
def mock_firebase_service():
    with patch("app.api.routes.users.firebase_service") as mock:
        yield mock

# --- Tests ---

def test_get_user_profile_me_privacy(mock_firebase_service):
    """My profile should have email (Private)"""
    mock_user = User(
        uid="me123",
        email="me@example.com",
        display_name="Me",
        role=UserRole.USER,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    # We call /api/users/profile which returns 'current_user' directly
    # dependency mock
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "me123", 
        "email": "me@example.com", 
        "role": "user",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    response = client.get("/api/users/profile")
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert data["email"] == "me@example.com"
    
    app.dependency_overrides = {}

def test_get_user_by_id_public(mock_firebase_service):
    """Other user profile should NOT have email (Public)"""
    mock_user = User(
        uid="other123",
        email="other@example.com",
        display_name="Other",
        role=UserRole.USER,
        created_at=datetime.utcnow(), 
        updated_at=datetime.utcnow()
    )
    mock_firebase_service.get_user_by_uid = AsyncMock(return_value=mock_user)
    
    # As anonymous user (or different user)
    app.dependency_overrides[get_optional_user] = lambda: None
    
    response = client.get("/api/users/profile/other123")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify Public Schema fields
    assert data["uid"] == "other123"
    assert data["display_name"] == "Other"
    
    # Verify Private fields are missing
    assert "email" not in data
    assert "phone_number" not in data
    
    app.dependency_overrides = {}

def test_get_user_by_id_owner(mock_firebase_service):
    """Owner viewing their own ID should see email (Private)"""
    mock_user = User(
        uid="me123",
        email="me@example.com",
        display_name="Me",
        role=UserRole.USER,
        created_at=datetime.utcnow(), 
        updated_at=datetime.utcnow()
    )
    mock_firebase_service.get_user_by_uid = AsyncMock(return_value=mock_user)
    
    # Logged in as me123
    app.dependency_overrides[get_optional_user] = lambda: {"uid": "me123", "role": "user"}
    
    response = client.get("/api/users/profile/me123")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify Private Schema fields are present
    assert "email" in data
    assert data["email"] == "me@example.com"
    
    app.dependency_overrides = {}
