from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture(autouse=True)
def patch_verify(monkeypatch):
    def fake_verify(token):
        if token == "faketoken":
            return {"uid": "testuid", "email": "test@example.com", "name": "Test User"}
        return None

    monkeypatch.setattr("app.services.auth_service.verify_id_token", fake_verify)


def test_register_returns_user():
    client = TestClient(app)
    r = client.post(
        "/api/auth/register", json={"idToken": "faketoken", "displayName": "Tester"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["uid"] == "testuid"
    assert data["displayName"] == "Tester"


def test_login_returns_user():
    client = TestClient(app)
    r = client.post("/api/auth/login", json={"idToken": "faketoken"})
    assert r.status_code == 200
    data = r.json()
    assert data["uid"] == "testuid"
    assert data["email"] == "test@example.com"
