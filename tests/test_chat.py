from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture(autouse=True)
def patch_verify_and_langchain(monkeypatch):
    def fake_verify(token):
        if token == "faketoken":
            return {"uid": "testuid", "email": "test@example.com", "name": "Test User"}
        return None

    async def fake_generate_response(session_id, user_id, user_message):
        return f"echo: {user_message}"

    async def fake_create_session(user_id, session_id):
        pass  # do nothing for test

    monkeypatch.setattr("app.services.auth_service.verify_id_token", fake_verify)
    monkeypatch.setattr(
        "app.services.langchain_service.generate_response", fake_generate_response
    )
    monkeypatch.setattr(
        "app.services.langchain_service.create_session", fake_create_session
    )


def test_create_session_and_send_message(patch_verify_and_langchain):
    client = TestClient(app)
    headers = {"Authorization": "Bearer faketoken"}
    r = client.post("/api/chat/session", headers=headers)
    assert r.status_code == 200
    sid = r.json()["sessionId"]

    r2 = client.post(
        "/api/chat/message",
        headers=headers,
        json={"sessionId": sid, "message": "Hello AI"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["sessionId"] == sid
    assert "echo: Hello AI" in data["reply"]
