from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, UTC

from app.main import app
from app.models.user import User, UserRole
from app.schemas.auth import AuthResponse, UserResponse, Token
from app.dependencies import get_current_user
from app.services.auth_service import AuthService
from app.utils.security import verify_refresh_token
from app.services.firebase_service import firebase_service

@pytest.fixture
def mock_user_instance():
    """Fixture to create a mock User instance."""
    return User(
        uid="mock_uid",
        email="mock@example.com",
        display_name="Mock User",
        role=UserRole.USER,
        phone_number=None,
        profile_picture=None,
        email_verified=True,
        created_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
        updated_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC),
    )

@pytest.fixture
def authenticated_client(monkeypatch, mock_user_instance):
    """
    Fixture that provides a TestClient with an overridden get_current_user dependency,
    simulating an authenticated user.
    """
    async def mock_get_current_user():
        return mock_user_instance

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield TestClient(app)
    app.dependency_overrides = {} # Clear overrides after test

def test_verify_token_returns_auth_response(monkeypatch, mock_user_instance):
    client = TestClient(app)

    # Mock the return value of auth_service.authenticate_with_social_provider
    mock_auth_service_return = {
        "user": mock_user_instance,
        "tokens": {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
        },
    }

    # Patch the authenticate_with_social_provider method
    monkeypatch.setattr(
        "app.services.auth_service.auth_service.authenticate_with_social_provider",
        AsyncMock(return_value=mock_auth_service_return),
    )
    # Make the request to the verify-token endpoint
    response = client.post("/api/v1/auth/verify-token", json={"idToken": "mock_id_token"})

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Validate the structure and content of the AuthResponse
    assert "user" in data
    assert "tokens" in data

    # Validate user data
    assert data["user"]["uid"] == mock_user_instance.uid
    assert data["user"]["email"] == mock_user_instance.email
    assert data["user"]["displayName"] == mock_user_instance.display_name
    assert data["user"]["role"] == mock_user_instance.role
    assert data["user"]["phoneNumber"] == mock_user_instance.phone_number
    assert data["user"]["profilePicture"] == mock_user_instance.profile_picture
    assert data["user"]["emailVerified"] == mock_user_instance.email_verified
    assert datetime.fromisoformat(data["user"]["createdAt"].replace('Z', '+00:00')) == mock_user_instance.created_at
    assert datetime.fromisoformat(data["user"]["updatedAt"].replace('Z', '+00:00')) == mock_user_instance.updated_at

    # Validate tokens data
    assert data["tokens"]["access_token"] == mock_auth_service_return["tokens"]["access_token"]
    assert data["tokens"]["refresh_token"] == mock_auth_service_return["tokens"]["refresh_token"]
    assert data["tokens"]["token_type"] == mock_auth_service_return["tokens"]["token_type"]
    assert data["tokens"]["expires_in"] == mock_auth_service_return["tokens"]["expires_in"]


def test_refresh_token_returns_new_tokens(monkeypatch, mock_user_instance):
    client = TestClient(app)

    # Mock the return value of verify_refresh_token from app.utils.security
    monkeypatch.setattr(
        "app.services.auth_service.verify_refresh_token",
        MagicMock(return_value={"sub": mock_user_instance.uid, "exp": 1234567890})
    )
    # Mock auth_service.firebase.get_user_by_uid
    monkeypatch.setattr(
        firebase_service,
        "get_user_by_uid",
        AsyncMock(return_value=mock_user_instance)
    )
    # Mock the return value of create_token_pair
    mock_new_tokens = {
        "access_token": "new_mock_access_token",
        "refresh_token": "new_mock_refresh_token",
        "token_type": "bearer",
        "expires_in": 3600,
    }
    monkeypatch.setattr(
        "app.services.auth_service.create_token_pair",
        MagicMock(return_value=mock_new_tokens)
    )
    # Make the request to the refresh endpoint
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "old_refresh_token"})

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Validate the structure and content of the Token response
    assert data["access_token"] == mock_new_tokens["access_token"]
    assert data["refresh_token"] == mock_new_tokens["refresh_token"]
    assert data["token_type"] == mock_new_tokens["token_type"]
    assert data["expires_in"] == mock_new_tokens["expires_in"]


def test_logout_returns_success(authenticated_client, monkeypatch, mock_user_instance):
    # Patch auth_service.logout_user to do nothing (simulate success)
    mock_logout = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "app.services.auth_service.auth_service.logout_user",
        mock_logout,
    )
    response = authenticated_client.post("/api/v1/auth/logout")

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}
    # Verify that logout_user was called with the correct UID
    assert mock_logout.call_args_list[0].args[0] == mock_user_instance.uid


def test_get_current_user_info_returns_user_data(authenticated_client, mock_user_instance):
    # Make the request to the /me endpoint
    response = authenticated_client.get("/api/v1/auth/me")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Validate the content of the UserResponse
    assert data["uid"] == mock_user_instance.uid
    assert data["email"] == mock_user_instance.email
    assert data["displayName"] == mock_user_instance.display_name
    assert data["role"] == mock_user_instance.role
    assert data["phoneNumber"] == mock_user_instance.phone_number
    # Note: Pydantic will convert datetime objects to ISO 8601 strings
    assert datetime.fromisoformat(data["createdAt"].replace('Z', '+00:00')) == mock_user_instance.created_at
    assert datetime.fromisoformat(data["updatedAt"].replace('Z', '+00:00')) == mock_user_instance.updated_at


