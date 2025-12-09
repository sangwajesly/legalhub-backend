import sys
from unittest.mock import MagicMock, patch, AsyncMock

# 1. Mock heavy dependencies BEFORE any app imports
faiss_mock = MagicMock()
faiss_mock.__spec__ = MagicMock()
sys.modules["faiss"] = faiss_mock

st_mock = MagicMock()
st_mock.__spec__ = MagicMock()
sys.modules["sentence_transformers"] = st_mock

# 2. Now import pytest and app
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import UserRole
from app.dependencies import get_current_user
client = TestClient(app)

@pytest.fixture
def mock_firebase_service():
    with patch("app.api.routes.cases.firebase_service") as mock:
        yield mock

@pytest.fixture
def mock_ingestion_service():
    with patch("app.api.routes.cases.ingestion_service") as mock:
        yield mock

@pytest.fixture
def mock_user_dependency():
    with patch("app.dependencies.verify_firebase_token") as mock:
        yield mock

# --- Tests ---

def test_list_cases_rbac_anonymous(mock_firebase_service):
    """Anonymous/Regular users cannot list all cases"""
    # Override current_user to be None (unauthenticated)
    app.dependency_overrides[get_current_user] = lambda: None
    
    response = client.get("/api/cases")
    assert response.status_code == 401

    # Override current_user to be Regular User
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": UserRole.USER, "email": "user@example.com"}
    
    response = client.get("/api/cases")
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

    # Clean up
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_list_cases_rbac_lawyer(mock_firebase_service):
    """Lawyers can list cases"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "l1", "role": UserRole.LAWYER}
    
    # Mock Firestore query
    mock_firebase_service.query_collection = AsyncMock(return_value=([], 0))
    
    response = client.get("/api/cases")
    assert response.status_code == 200
    app.dependency_overrides = {}

def test_get_case_rbac_owner(mock_firebase_service):
    """Owner can view their case"""
    case_data = {
        "caseId": "c1",
        "userId": "u1",
        "title": "My Case",
        "description": "Description must be at least 20 characters long to pass validation.",
        "status": "submitted",
        "category": "civil",
        "createdAt": "2024-01-01T00:00:00+00:00",
        "updatedAt": "2024-01-01T00:00:00+00:00"
    }
    mock_firebase_service.get_document = AsyncMock(return_value=case_data)
    mock_firebase_service.update_document = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": UserRole.USER}
    
    response = client.get("/api/cases/c1")
    assert response.status_code == 200
    assert response.json()["title"] == "My Case"
    app.dependency_overrides = {}

def test_get_case_rbac_forbidden(mock_firebase_service):
    """Non-owner regular user cannot view case"""
    case_data = {
        "caseId": "c1",
        "userId": "u1", # Owned by u1
        "title": "My Case",
        "status": "submitted"
    }
    mock_firebase_service.get_document = AsyncMock(return_value=case_data)

    # Request as u2
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u2", "role": UserRole.USER}
    
    response = client.get("/api/cases/c1")
    assert response.status_code == 403
    app.dependency_overrides = {}

def test_create_case_anonymous(mock_firebase_service):
    """Test creating an anonymous case"""
    app.dependency_overrides[get_current_user] = lambda: None
    mock_firebase_service.set_document = AsyncMock()
    
    payload = {
        "category": "civil",
        "title": "Anon Case",
        "description": "This is a detailed description of the anonymous case.",
        "isAnonymous": True,
        "email": "anon@example.com",
        "contactName": "Anon"
    }
    
    response = client.post("/api/cases/", json=payload)
    assert response.status_code == 201
    assert response.json()["isAnonymous"] is True
    app.dependency_overrides = {}

def test_get_case_stats_admin_only(mock_firebase_service):
    """Only admin can get stats"""
    mock_firebase_service.query_collection = AsyncMock(return_value=([], 0))
    
    # As lawyer (should fail)
    app.dependency_overrides[get_current_user] = lambda: {"uid": "l1", "role": UserRole.LAWYER}
    response = client.get("/api/cases/stats/overview")
    assert response.status_code == 403
    
    # As Admin
    app.dependency_overrides[get_current_user] = lambda: {"uid": "a1", "role": UserRole.ADMIN, "is_admin": True}
    response = client.get("/api/cases/stats/overview")
    assert response.status_code == 200
    app.dependency_overrides = {}
