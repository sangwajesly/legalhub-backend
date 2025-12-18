"""
Verification script to ensure all Pydantic models correctly map camelCase Firestore data to snake_case attributes,
and that response schemas correctly support validation from model instances (from_attributes=True).
"""

import json
from datetime import datetime, timezone
from pydantic import ValidationError
from app.models.user import User
from app.models.article import Article
from app.models.lawyer import Lawyer
from app.models.organization import Organization
from app.models.booking import Booking
from app.models.case import Case
from app.models.chat import ChatSession, ChatMessage
from app.models.communication import DirectMessage
from app.schemas.auth import UserResponse


def verify_model(model_class, sample_data, model_name):
    print(f"--- Verifying {model_name} (from dict) ---")
    try:
        instance = model_class.model_validate(sample_data)
        print(f"SUCCESS: {model_name} validated from dictionary.")
        return instance
    except ValidationError as e:
        print(f"FAILED: {model_name} validation error:")
        print(e)
    except Exception as e:
        print(f"ERROR: {model_name} unexpected error: {e}")
    return None


def verify_from_instance(response_class, instance, name):
    print(f"--- Verifying {name} (from instance) ---")
    try:
        resp = response_class.model_validate(instance)
        print(f"SUCCESS: {name} validated from model instance.")
        return resp
    except ValidationError as e:
        print(
            f"FAILED: {name} validation error (attributes missing or from_attributes=False):")
        print(e)
    except Exception as e:
        print(f"ERROR: {name} unexpected error: {e}")
    return None


def main():
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. User & UserResponse
    user_data = {
        "uid": "user_123",
        "email": "test@example.com",
        "displayName": "Test User",
        "role": "user",
        "emailVerified": True,
        "phoneNumber": "+1234567890",
        "createdAt": now_iso,
        "updatedAt": now_iso
    }
    user_instance = verify_model(User, user_data, "User")
    if user_instance:
        verify_from_instance(UserResponse, user_instance, "UserResponse")

    # 2. Article
    article_data = {
        "articleId": "article_123",
        "title": "Test Article",
        "slug": "test-article",
        "content": "This is a test article content with sufficient length for validation.",
        "authorId": "user_123",
        "tags": ["test", "verify"],
        "published": True,
        "createdAt": now_iso,
        "updatedAt": now_iso,
        "likesCount": 10,
        "views": 100
    }
    verify_model(Article, article_data, "Article")

    # 3. Lawyer
    lawyer_data = {
        "uid": "lawyer_123",
        "displayName": "Jane Lawyer",
        "email": "jane@lawyer.com",
        "licenseNumber": "BAR-456",
        "practiceAreas": ["Civil", "Family"],
        "hourlyRate": 150.0,
        "yearsExperience": 10,
        "verified": True,
        "createdAt": now_iso,
        "updatedAt": now_iso
    }
    verify_model(Lawyer, lawyer_data, "Lawyer")

    # 4. Organization
    org_data = {
        "uid": "org_123",
        "displayName": "Legal Aid Org",
        "email": "info@legalaid.org",
        "registrationNumber": "REG-789",
        "organizationType": "NGO",
        "contactPerson": "Manager Name",
        "createdAt": now_iso,
        "updatedAt": now_iso
    }
    verify_model(Organization, org_data, "Organization")

    # 5. Booking
    booking_data = {
        "bookingId": "booking_123",
        "lawyerId": "lawyer_123",
        "userId": "user_123",
        "consultationType": "call",
        "scheduledAt": now_iso,
        "duration": 60,
        "paymentStatus": "paid",
        "createdAt": now_iso,
        "updatedAt": now_iso
    }
    verify_model(Booking, booking_data, "Booking")

    # 6. Case
    case_data = {
        "caseId": "case_123",
        "userId": "user_123",
        "category": "civil",
        "title": "Test Case Title",
        "description": "This is a test case description with enough length to pass validation rules of min_length=20.",
        "status": "submitted",
        "isAnonymous": False,
        "contactName": "John Contact",
        "createdAt": now_iso,
        "updatedAt": now_iso
    }
    verify_model(Case, case_data, "Case")

    # 7. Chat
    chat_msg_data = {
        "id": "msg_123",
        "role": "user",
        "text": "Hello world",
        "userId": "user_123",
        "createdAt": now_iso
    }
    verify_model(ChatMessage, chat_msg_data, "ChatMessage")

    # 8. DirectMessage
    dm_data = {
        "id": "dm_123",
        "senderId": "user_123",
        "receiverId": "lawyer_123",
        "content": "Hello lawyer",
        "timestamp": now_iso,
        "read": False,
        "bookingId": "booking_123"
    }
    verify_model(DirectMessage, dm_data, "DirectMessage")


if __name__ == "__main__":
    main()
