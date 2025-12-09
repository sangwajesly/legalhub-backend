import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Mock deps
faiss_mock = MagicMock()
faiss_mock.__spec__ = MagicMock()
sys.modules["faiss"] = faiss_mock
st_mock = MagicMock()
st_mock.__spec__ = MagicMock()
sys.modules["sentence_transformers"] = st_mock

from app.main import app
from app.dependencies import get_current_user

client = TestClient(app)

@pytest.fixture
def mock_payment_service():
    with patch("app.api.routes.payments.payment_service") as mock:
        yield mock

def test_initiate_stripe_payment(mock_payment_service):
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user1", "role": "user"}
    
    mock_response = {
        "transactionId": "txn_123",
        "paymentUrl": "https://fake.stripe.com/pay"
    }
    mock_payment_service.initiate_payment = AsyncMock(return_value=mock_response)
    
    payload = {
        "bookingId": "bk_1",
        "provider": "stripe",
        "returnUrl": "http://localhost:3000/success"
    }
    
    response = client.post("/api/payments/initiate", json=payload)
    
    assert response.status_code == 200
    assert response.json()["paymentUrl"] == "https://fake.stripe.com/pay"
    
    app.dependency_overrides = {}

def test_initiate_mtn_payment(mock_payment_service):
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user1", "role": "user"}
    
    mock_response = {
        "transactionId": "txn_456",
        "message": "Push sent"
    }
    mock_payment_service.initiate_payment = AsyncMock(return_value=mock_response)
    
    payload = {
        "bookingId": "bk_2",
        "provider": "mtn_momo",
        "currency": "RWF"
    }
    
    response = client.post("/api/payments/initiate", json=payload)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Push sent"

    app.dependency_overrides = {}
