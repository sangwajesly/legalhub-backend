from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture(autouse=True)
def patch_auth_and_firebase(monkeypatch):
    # Fake auth verification
    def fake_verify(token):
        if token == "faketoken":
            return {
                "uid": "testuid",
                "email": "test@example.com",
                "name": "Test User",
                "is_admin": True,
            }
        return None

    monkeypatch.setattr("app.services.auth_service.verify_id_token", fake_verify)

    # In-memory store to simulate Firestore
    store = {}

    async def fake_set_document(path: str, data: dict):
        # simple path like "cases/case_123"
        store[path] = data

    async def fake_get_document(path: str):
        return store.get(path)

    async def fake_update_document(path: str, data: dict):
        # merge update into existing doc
        existing = store.get(path, {})
        existing.update(data)
        store[path] = existing

    async def fake_query_collection(collection: str, filters=None, limit=20, offset=0):
        # return list of (doc_id, doc_data) tuples and total_count
        docs = []
        prefix = f"{collection}/"
        for k, v in store.items():
            if k.startswith(prefix):
                doc_id = k.split("/", 1)[1]
                match = True
                if filters:
                    for fk, fv in filters.items():
                        if v.get(fk) != fv:
                            match = False
                            break
                if match:
                    docs.append((doc_id, v))
        total = len(docs)
        # apply offset/limit
        docs_page = docs[offset : offset + limit]
        return docs_page, total

    async def fake_upload_file(path: str, content: bytes, content_type: str):
        # return a fake download URL
        return f"https://storage.fake/{path}"

    monkeypatch.setattr(
        "app.services.firebase_service.set_document", fake_set_document, raising=False
    )
    monkeypatch.setattr(
        "app.services.firebase_service.get_document", fake_get_document, raising=False
    )
    monkeypatch.setattr(
        "app.services.firebase_service.update_document",
        fake_update_document,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.firebase_service.query_collection",
        fake_query_collection,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.firebase_service.upload_file", fake_upload_file, raising=False
    )


def test_create_case_anonymous(patch_auth_and_firebase):
    client = TestClient(app)
    headers = {"Authorization": "Bearer faketoken"}
    payload = {
        "category": "criminal",
        "title": "Test anonymous",
        "description": "This is a test anonymous case description that is long enough.",
        "isAnonymous": True,
        "email": "anon@example.com",
        "contactName": "Anon Reporter",
        "priority": "high",
        "tags": ["test"],
    }

    r = client.post("/api/cases/", headers=headers, json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["isAnonymous"] is True
    assert data["title"] == payload["title"]


def test_get_and_list_cases(patch_auth_and_firebase):
    client = TestClient(app)
    headers = {"Authorization": "Bearer faketoken"}

    # Create two cases via direct POST
    payload1 = {
        "category": "civil",
        "title": "Case One",
        "description": "Detailed description for case one that is sufficiently long.",
        "isAnonymous": False,
        "contactName": "User One",
    }

    payload2 = {
        "category": "criminal",
        "title": "Case Two",
        "description": "Detailed description for case two that is sufficiently long.",
        "isAnonymous": True,
        "email": "two@example.com",
        "contactName": "Reporter Two",
    }

    r1 = client.post("/api/cases/", headers=headers, json=payload1)
    assert r1.status_code == 201
    id1 = r1.json()["caseId"]

    r2 = client.post("/api/cases/", headers=headers, json=payload2)
    assert r2.status_code == 201
    id2 = r2.json()["caseId"]

    # Get first case
    g = client.get(f"/api/cases/{id1}", headers=headers)
    assert g.status_code == 200
    assert g.json()["caseId"] == id1

    # List cases without filters
    L = client.get("/api/cases", headers=headers)
    assert L.status_code == 200
    body = L.json()
    assert "cases" in body
    assert body["total"] >= 2


def test_upload_attachment_and_attachment_present(patch_auth_and_firebase):
    client = TestClient(app)
    headers = {"Authorization": "Bearer faketoken"}

    # Create an identified case (userId will be set)
    payload = {
        "category": "civil",
        "title": "Attachment Case",
        "description": "Long enough description for attachment test.",
        "isAnonymous": False,
        "contactName": "Uploader",
    }
    r = client.post("/api/cases/", headers=headers, json=payload)
    assert r.status_code == 201
    case_id = r.json()["caseId"]

    # Upload a small file
    files = {"file": ("evidence.txt", b"hello world", "text/plain")}
    up = client.post(f"/api/cases/{case_id}/attachments", headers=headers, files=files)
    assert up.status_code == 201
    up_body = up.json()
    assert "attachmentId" in up_body

    # Fetch the case and ensure attachment exists
    g = client.get(f"/api/cases/{case_id}", headers=headers)
    assert g.status_code == 200
    case_body = g.json()
    assert "attachments" in case_body
    assert any(a.get("fileName") == "evidence.txt" for a in case_body["attachments"])


def test_update_case_status_authorized(patch_auth_and_firebase):
    client = TestClient(app)
    headers = {"Authorization": "Bearer faketoken"}

    # Create a case
    payload = {
        "category": "labor",
        "title": "Status Case",
        "description": "Detailed description for status change test.",
        "isAnonymous": False,
        "contactName": "Owner",
    }
    r = client.post("/api/cases/", headers=headers, json=payload)
    assert r.status_code == 201
    case_id = r.json()["caseId"]

    # Update status to in_progress
    status_payload = {"status": "in_progress", "notes": "Taking the case"}
    up = client.put(
        f"/api/cases/{case_id}/status", headers=headers, json=status_payload
    )
    assert up.status_code == 200
    assert up.json()["status"] == "in_progress"


def test_user_cases_only_owner_or_admin(patch_auth_and_firebase):
    client = TestClient(app)
    headers = {"Authorization": "Bearer faketoken"}

    # Create a case (user is testuid)
    payload = {
        "category": "property",
        "title": "Owner Case",
        "description": "Owner's case description.",
        "isAnonymous": False,
        "contactName": "Owner",
    }
    r = client.post("/api/cases/", headers=headers, json=payload)
    assert r.status_code == 201
    case_id = r.json()["caseId"]

    # Request cases for the current user
    L = client.get(f"/api/cases/user/testuid", headers=headers)
    assert L.status_code == 200
    assert any(c.get("caseId") == case_id for c in L.json().get("cases", []))


def test_anonymous_creation_validation(patch_auth_and_firebase):
    client = TestClient(app)
    headers = {"Authorization": "Bearer faketoken"}

    # Missing email and contactName for anonymous should be 400
    payload = {
        "category": "criminal",
        "title": "Bad Anonymous",
        "description": "Too short? no — long enough to pass length checks.",
        "isAnonymous": True,
    }
    r = client.post("/api/cases/", headers=headers, json=payload)
    assert r.status_code == 400
