import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.firebase_service import FirebaseService
from app.services.firebase_mcp_client import FirebaseMcpClient
from app.models.user import User


@pytest.fixture
def mock_firebase_service():
    """Fixture to provide a mocked FirebaseService instance."""
    return AsyncMock(spec=FirebaseService)


@pytest.fixture
def firebase_mcp_client(mock_firebase_service):
    """Fixture to provide a FirebaseMcpClient instance with a mocked FirebaseService."""
    return FirebaseMcpClient(firebase_service=mock_firebase_service)


@pytest.mark.asyncio
async def test_get_user_by_uid(firebase_mcp_client, mock_firebase_service):
    """
    Test that get_user_by_uid in FirebaseMcpClient correctly calls
    the underlying FirebaseService's get_user_by_uid method.
    """
    test_uid = "test_user_id"
    expected_user = User(
        uid=test_uid,
        email="test@example.com",
        display_name="Test User",
        role="user",
    )
    mock_firebase_service.get_user_by_uid.return_value = expected_user

    user = await firebase_mcp_client.get_user_by_uid(test_uid)

    mock_firebase_service.get_user_by_uid.assert_called_once_with(test_uid)
    assert user == expected_user


@pytest.mark.asyncio
async def test_create_user(firebase_mcp_client, mock_firebase_service):
    """
    Test that create_user in FirebaseMcpClient correctly calls
    the underlying FirebaseService's create_user method.
    """
    email = "newuser@example.com"
    password = "password123"
    display_name = "New User"
    role = "user"
    phone_number = "+1234567890"

    expected_user = User(
        uid="new_user_id",
        email=email,
        display_name=display_name,
        role=role,
        phone_number=phone_number,
    )
    mock_firebase_service.create_user.return_value = expected_user

    user = await firebase_mcp_client.create_user(
        email=email,
        password=password,
        display_name=display_name,
        role=role,
        phone_number=phone_number,
    )

    mock_firebase_service.create_user.assert_called_once_with(
        email, password, display_name, role, phone_number
    )
    assert user == expected_user


@pytest.mark.asyncio
async def test_upload_file(firebase_mcp_client, mock_firebase_service):
    """
    Test that upload_file in FirebaseMcpClient correctly calls
    the underlying FirebaseService's upload_file method.
    """
    path = "test/path/to/file.txt"
    content = b"file content"
    content_type = "text/plain"
    expected_url = "http://firebase.storage/file.txt"

    mock_firebase_service.upload_file.return_value = expected_url

    url = await firebase_mcp_client.upload_file(
        path=path, content=content, content_type=content_type
    )

    mock_firebase_service.upload_file.assert_called_once_with(
        path, content, content_type
    )
    assert url == expected_url
