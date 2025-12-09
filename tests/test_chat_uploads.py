import sys
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Mock heavy dependencies BEFORE imports
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
    with patch("app.services.langchain_service.gemini_service") as mock:
        yield mock

@pytest.fixture
def mock_firebase_service():
    with patch("app.services.langchain_service.firebase_service") as mock:
        # Important: Mock get_chat_history to return empty list
        mock.get_chat_history = AsyncMock(return_value=[])
        mock.add_chat_message = AsyncMock()
        mock.create_chat_session = AsyncMock()
        mock.get_user_chat_sessions = AsyncMock(return_value=[])
        yield mock

@pytest.fixture
def mock_file_service():
    with patch("app.api.routes.chat.file_service.file_service") as mock:
        yield mock

@pytest.fixture
def mock_file_service_internal():
    # Mock the one used inside langchain_service
    with patch("app.services.langchain_service.file_service.file_service") as mock:
        yield mock

# --- Tests ---

def test_upload_file_route(mock_file_service):
    """Test POST /api/chat/upload"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": "user"}
    
    mock_file_service.save_upload = AsyncMock(return_value="file-123.jpg")
    
    files = {"file": ("test.jpg", b"fakecontent", "image/jpeg")}
    response = client.post("/api/chat/upload", files=files)
    
    assert response.status_code == 200
    assert response.json()["fileId"] == "file-123.jpg"
    
    app.dependency_overrides = {}

def test_chat_message_with_image_attachment(
    mock_gemini_service, 
    mock_firebase_service,
    mock_file_service_internal
):
    """Test sending message with image attachment triggers multimodal Gemini call"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": "user"}
    
    # Setup Mocks
    mock_file_service_internal.get_file_path = MagicMock()
    # Create a mock path object that behaves like Path
    path_mock = MagicMock()
    path_mock.read_bytes.return_value = b"fakeimagebytes"
    mock_file_service_internal.get_file_path.return_value = path_mock
    
    # Helper to mock mimetypes.guess_type
    with patch("mimetypes.guess_type", return_value=("image/jpeg", None)):
        
        mock_gemini_service.send_message = AsyncMock(return_value={"response": "I see the image"})
        
        payload = {
            "message": "What is this?",
            "sessionId": "sess1",
            "attachments": ["file-123.jpg"]
        }
        
        response = client.post("/api/chat/message", json=payload)
        
        assert response.status_code == 200
        assert response.json()["reply"] == "I see the image"
        
        # Verify gemini was called with images
        call_args = mock_gemini_service.send_message.call_args
        # send_message(prompt, images=[...])
        assert call_args is not None
        _, kwargs = call_args
        assert "images" in kwargs
        assert len(kwargs["images"]) == 1
        assert kwargs["images"][0]["mime_type"] == "image/jpeg"

    app.dependency_overrides = {}

def test_chat_message_with_pdf_attachment(
    mock_gemini_service,
    mock_firebase_service,
    mock_file_service_internal
):
    """Test sending message with PDF extracts text and appends to prompt"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": "user"}

    # Setup Mocks
    path_mock = MagicMock()
    path_mock.__str__.return_value = "/tmp/fake.pdf"
    mock_file_service_internal.get_file_path.return_value = path_mock
    
    # Mock text extraction
    with patch("app.services.langchain_service.extract_text_from_pdf", return_value="PDF CONTENT HERE") as mock_extract:
        with patch("mimetypes.guess_type", return_value=("application/pdf", None)):
            
            mock_gemini_service.send_message = AsyncMock(return_value={"response": "Analyzed PDF"})
            
            payload = {
                "message": "Analyze this",
                "sessionId": "sess1",
                "attachments": ["contract.pdf"]
            }
            
            response = client.post("/api/chat/message", json=payload)
            
            assert response.status_code == 200
            
            # Verify Prompt contains extracted text
            call_args = mock_gemini_service.send_message.call_args
            prompt_arg = call_args[0][0]
            assert "PDF CONTENT HERE" in prompt_arg
            
    app.dependency_overrides = {}
