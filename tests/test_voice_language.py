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
from app.dependencies import get_current_user

client = TestClient(app)

@pytest.fixture
def mock_gemini_service():
    with patch("app.api.routes.utils.gemini_service") as mock:
        yield mock

@pytest.fixture
def mock_firebase_service():
    with patch("app.api.routes.users.firebase_service") as mock:
        yield mock

# --- Tests ---

def test_transcribe_audio_success(mock_gemini_service):
    """Test audio transcription endpoint"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": "user"}
    
    mock_gemini_service.transcribe_audio = AsyncMock(return_value="Hello world")
    
    # Mock file upload
    files = {"file": ("test.webm", b"fakeaudiobytes", "audio/webm")}
    
    response = client.post("/api/utils/transcribe", files=files)
    
    assert response.status_code == 200
    assert response.json()["text"] == "Hello world"
    mock_gemini_service.transcribe_audio.assert_called_once()
    
    app.dependency_overrides = {}

def test_transcribe_audio_invalid_file(mock_gemini_service):
    """Test invalid file type"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": "user"}
    
    files = {"file": ("test.txt", b"text content", "text/plain")}
    
    response = client.post("/api/utils/transcribe", files=files)
    
    assert response.status_code == 400
    
    app.dependency_overrides = {}

def test_update_language_preference(mock_firebase_service):
    """Test updating user language preference"""
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "u1", 
        "role": "user", 
        "email": "u1@example.com",
        "email_verified": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Mock update_user (main) and update_user_profile (extended)
    mock_firebase_service.update_user = AsyncMock(return_value={"uid": "u1", "role": "user"})
    mock_firebase_service.update_user_profile = AsyncMock()
    
    payload = {
        "language_preference": "fr"
    }
    
    response = client.put("/api/users/profile", json=payload)
    
    assert response.status_code == 200
    
    # Verify update_user_profile was called with correct dict
    args = mock_firebase_service.update_user_profile.call_args
    assert args[0][0] == "u1" # uid
    assert args[0][1]["language_preference"] == "fr"
    
    app.dependency_overrides = {}
