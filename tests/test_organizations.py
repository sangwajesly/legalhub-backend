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

def test_list_organizations_mocked(monkeypatch):
    store = {}

    async def query_docs(collection, filters=None, limit=20, offset=0):
        docs = []
        for path, data in store.items():
            if path.startswith(f"{collection}/"):
                # Filter mock if needed, but for simple list likely not needed for this test
                # unless we want to test filtering specifically
                docs.append((path.split("/")[-1], data))
        return docs, len(docs)

    monkeypatch.setattr(firebase_service, "query_collection", query_docs, raising=False)

    # put two organizations
    store["organizations/org_1"] = {
        "displayName": "NGO A",
        "organizationType": "NGO",
        "location": "City X"
    }
    store["organizations/org_2"] = {
        "displayName": "Firm B",
        "organizationType": "Law Firm",
        "location": "City Y"
    }

    client = TestClient(app)
    r = client.get("/api/organizations")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["organizations"]) == 2
    assert data["organizations"][0]["display_name"] == "NGO A"


def test_create_update_delete_organization(monkeypatch):
    store = {}

    async def set_doc(path, data):
        store[path] = data

    async def get_doc(path):
        return store.get(path)

    async def update_doc(path, data):
        if path in store:
            store[path].update(data)
        else:
            store[path] = data

    async def delete_doc(path):
        if path in store:
            del store[path]

    monkeypatch.setattr(firebase_service, "set_document", set_doc, raising=False)
    monkeypatch.setattr(firebase_service, "get_document", get_doc, raising=False)
    monkeypatch.setattr(firebase_service, "update_document", update_doc, raising=False)
    monkeypatch.setattr(firebase_service, "delete_document", delete_doc, raising=False)

    # override auth
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "org_new",
        "is_admin": False,
    }
    client = TestClient(app)

    # Create
    r = client.post(
        "/api/organizations",
        json={
            "display_name": "New Org",
            "email": "new@org.com",
            "organization_type": "NGO",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["uid"] == "org_new"
    assert data["display_name"] == "New Org"

    # Update
    r2 = client.put("/api/organizations/org_new", json={"bio": "We help people"})
    assert r2.status_code == 200
    assert store.get("organizations/org_new").get("bio") == "We help people"

    # Delete
    r3 = client.delete("/api/organizations/org_new")
    assert r3.status_code == 200
    assert "organizations/org_new" not in store

    app.dependency_overrides.clear()
