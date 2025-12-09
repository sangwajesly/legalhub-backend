import sys
from unittest.mock import MagicMock, patch, AsyncMock

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

client = TestClient(app)

@pytest.fixture
def mock_firebase_service():
    with patch("app.api.routes.articles.firebase_service") as mock:
        yield mock

# --- Tests ---

def test_list_articles_pagination(mock_firebase_service):
    """Test efficient pagination"""
    # Mock return value
    mock_firebase_service.query_collection = AsyncMock(return_value=([], 0))
    
    response = client.get("/api/articles?page=2&pageSize=10")
    
    # Verify calls
    assert mock_firebase_service.query_collection.called
    kwargs = mock_firebase_service.query_collection.call_args.kwargs
    assert kwargs["limit"] == 10
    assert kwargs["offset"] == 10
    assert kwargs["filters"]["published"] is True

def test_create_article_rbac_user(mock_firebase_service):
    """Regular user cannot publish article"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "u1", "role": "user"}
    
    response = client.post("/api/articles/", json={
        "title": "My Article",
        "content": "Content",
        "tags": [],
        "published": True
    })
    
    assert response.status_code == 403
    app.dependency_overrides = {}

def test_create_article_rbac_lawyer(mock_firebase_service):
    """Lawyer can publish article"""
    app.dependency_overrides[get_current_user] = lambda: {"uid": "l1", "role": UserRole.LAWYER}
    doc_ref_mock = MagicMock()
    doc_ref_mock.id = "new_article_id"
    mock_firebase_service.db.collection.return_value.document.return_value = doc_ref_mock
    
    response = client.post("/api/articles/", json={
        "title": "Legal Advice",
        "content": "Content...",
        "tags": ["law"],
        "published": True
    })
    
    assert response.status_code == 201
    app.dependency_overrides = {}
