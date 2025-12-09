import sys
from unittest.mock import MagicMock
faiss_mock = MagicMock()
faiss_mock.__spec__ = MagicMock()
sys.modules["faiss"] = faiss_mock
st_mock = MagicMock()
st_mock.__spec__ = MagicMock()
sys.modules["sentence_transformers"] = st_mock

from fastapi.testclient import TestClient
from app.main import app
from app.services import firebase_service
from app.dependencies import get_current_user
from app.models.user import UserRole, User


def test_lawyer_dashboard_stats(monkeypatch):
    store = {}
    
    # Mock firebase methods
    async def get_doc(path):
        return store.get(path)

    async def query_docs(collection, filters=None, limit=20, offset=0):
        # Very simple mock matching
        res = []
        if collection == "cases":
             # Should match lawyerId == lawyer_stats_test
             res = [("c1", {})] 
        elif collection == "bookings":
             res = [("b1", {}), ("b2", {})]
        return res, len(res)

    monkeypatch.setattr(firebase_service, "get_document", get_doc, raising=False)
    monkeypatch.setattr(firebase_service, "query_collection", query_docs, raising=False)

    # Setup Lawyer Profile
    store["lawyers/lawyer_stats_test"] = {
        "rating": 4.5,
        "numReviews": 10,
        "views": 100
    }

    # Mock Auth as Lawyer
    app.dependency_overrides[get_current_user] = lambda: User(
        uid="lawyer_stats_test",
        email="lawyer@test.com",
        display_name="Test Lawyer",
        role=UserRole.LAWYER
    )
    
    client = TestClient(app)
    r = client.get("/api/analytics/lawyer")
    
    assert r.status_code == 200
    data = r.json()
    assert data["total_views"] == 100
    assert data["active_cases"] == 1
    assert data["total_bookings"] == 2
    assert data["raw_rating"] == 4.5
    
    app.dependency_overrides.clear()


def test_organization_dashboard_stats(monkeypatch):
    store = {}
    
    async def get_doc(path):
        return store.get(path)
        
    monkeypatch.setattr(firebase_service, "get_document", get_doc, raising=False)
    
    # Setup Org Profile
    store["organizations/org_stats_test"] = {
        "verified": True,
        "views": 50
    }

    # Mock Auth as Organization
    app.dependency_overrides[get_current_user] = lambda: User(
        uid="org_stats_test",
        email="org@test.com",
        display_name="Test Org",
        role=UserRole.ORGANIZATION
    )

    client = TestClient(app)
    r = client.get("/api/analytics/organization")
    
    assert r.status_code == 200
    data = r.json()
    assert data["total_views"] == 50
    assert data["verified"] is True
    
    app.dependency_overrides.clear()


def test_wrong_role_access(monkeypatch):
    # Mock Auth as User (accessing lawyer stats)
    app.dependency_overrides[get_current_user] = lambda: User(
        uid="just_user",
        email="user@test.com",
        display_name="Test User",
        role=UserRole.USER
    )
    
    client = TestClient(app)
    r = client.get("/api/analytics/lawyer")
    assert r.status_code == 403 # Forbidden
    
    r = client.get("/api/analytics/organization")
    assert r.status_code == 403 # Forbidden
    
    app.dependency_overrides.clear()
