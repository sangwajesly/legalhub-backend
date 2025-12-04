"""
Firebase service for Firestore and Authentication operations
"""

from __future__ import annotations
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import os
import json
import tempfile

from app.config import settings
from app.models.user import (
    User,
    UserProfile,
)
from app.models.chat import ChatMessage


# Helper function to convert the custom User model to a Firestore-safe dictionary
def user_to_firestore_dict(user_model: User) -> Dict[str, Any]:
    """Converts a User model instance to a dictionary, handling datetime conversion."""

    # Try Pydantic V2 method first, then V1 method
    try:
        user_dict = user_model.model_dump()
    except AttributeError:
        # Fallback for Pydantic V1 or similar models
        user_dict = user_model.dict()

    return user_dict


class FirebaseService:
    """Service for Firebase operations"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern to ensure only one Firebase instance"""
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Firebase Admin SDK"""
        if not FirebaseService._initialized:
            self._initialize_firebase()
            self.db = firestore.client()
            FirebaseService._initialized = True

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with credentials"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            print("Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            if settings.DEV_MODE and settings.FIREBASE_EMULATOR_HOST:
                # Use emulator for development
                os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIREBASE_EMULATOR_HOST
                firebase_admin.initialize_app()
                print(f"Firebase initialized with emulator: {settings.FIREBASE_EMULATOR_HOST}")
            else:
                # Production: Support both file path and JSON string
                cred = None
                
                # Option 1: Try to load from JSON string (preferred for Render/production)
                if settings.FIREBASE_CREDENTIALS_JSON:
                    try:
                        # Parse the JSON string
                        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                        cred = credentials.Certificate(cred_dict)
                        print("Firebase initialized with JSON credentials from environment")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing FIREBASE_CREDENTIALS_JSON: {e}")
                        raise ValueError("Invalid FIREBASE_CREDENTIALS_JSON format")
                
                # Option 2: Try to load from file path (for local development)
                elif settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    print(f"Firebase initialized with credentials from: {settings.FIREBASE_CREDENTIALS_PATH}")
                
                else:
                    raise ValueError(
                        "Firebase credentials not found. Please set either:\n"
                        "1. FIREBASE_CREDENTIALS_JSON (recommended for production)\n"
                        "2. FIREBASE_CREDENTIALS_PATH pointing to a valid credentials file"
                    )
                
                # Initialize with credentials
                if cred:
                    firebase_admin.initialize_app(
                        cred, {"storageBucket": settings.FIREBASE_STORAGE_BUCKET}
                    )
                    print("Firebase initialized successfully")

    # ============================================
    # USER OPERATIONS
    # ============================================

    async def create_user(
        self,
        email: str,
        password: str,
        display_name: str,
        role: str = "user",
        phone_number: Optional[str] = None,
    ) -> User:
        """Create a new user in Firebase Authentication and Firestore"""
        try:
            firebase_user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                phone_number=phone_number,
            )

            user = User(
                uid=firebase_user.uid,
                email=email,
                display_name=display_name,
                role=role,
                phone_number=phone_number,
                email_verified=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                profile_picture=(
                    firebase_user.photo_url
                    if hasattr(firebase_user, "photo_url")
                    else None
                ),
            )

            firestore_data = user_to_firestore_dict(user)
            self.db.collection("users").document(firebase_user.uid).set(firestore_data)

            return user

        except firebase_auth.EmailAlreadyExistsError:
            raise ValueError("Email already exists")
        except Exception as e:
            print(f"DEBUG: Failed to create user or save to Firestore: {str(e)}")
            raise Exception(f"Error creating user: {str(e)}")

    async def get_user_by_uid(self, uid: str) -> Optional[User]:
        """Get user by UID from Firestore"""
        try:
            doc = self.db.collection("users").document(uid).get()
            if doc.exists:
                doc_data = doc.to_dict()
                doc_data["uid"] = uid
                return User.model_validate(doc_data)
            return None
        except Exception as e:
            raise Exception(f"Error getting user: {str(e)}")

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from Firestore"""
        try:
            users_ref = self.db.collection("users")
            query = users_ref.where("email", "==", email).limit(1).stream()

            for doc in query:
                doc_data = doc.to_dict()
                doc_data["uid"] = doc.id
                return User.model_validate(doc_data)

            return None
        except Exception as e:
            raise Exception(f"Error getting user by email: {str(e)}")

    async def update_user(self, uid: str, data: Dict[str, Any]) -> User:
        """Update user information in Firestore"""
        try:
            data["updated_at"] = datetime.now(timezone.utc)
            user_ref = self.db.collection("users").document(uid)
            user_ref.update(data)

            if "display_name" in data:
                firebase_auth.update_user(uid, display_name=data["display_name"])

            return await self.get_user_by_uid(uid)

        except Exception as e:
            raise Exception(f"Error updating user: {str(e)}")

    async def delete_user(self, uid: str) -> bool:
        """Delete user from Firebase Authentication and Firestore"""
        try:
            firebase_auth.delete_user(uid)
            self.db.collection("users").document(uid).delete()
            return True
        except Exception as e:
            raise Exception(f"Error deleting user: {str(e)}")

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token"""
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            raise Exception(f"Invalid token: {str(e)}")

    # ============================================
    # USER PROFILE OPERATIONS
    # ============================================

    async def get_user_profile(self, uid: str) -> Optional[UserProfile]:
        """Get user profile from Firestore"""
        try:
            doc = self.db.collection("user_profiles").document(uid).get()
            if doc.exists:
                doc_data = doc.to_dict()
                doc_data["uid"] = uid
                return UserProfile.model_validate(doc_data)
            return None
        except Exception as e:
            raise Exception(f"Error getting user profile: {str(e)}")

    async def update_user_profile(
        self, uid: str, profile_data: Dict[str, Any]
    ) -> UserProfile:
        """Update or create user profile"""
        try:
            profile_ref = self.db.collection("user_profiles").document(uid)
            doc = profile_ref.get()
            
            if not doc.exists:
                profile = UserProfile(uid=uid, **profile_data)
                try:
                    profile_dict = profile.model_dump()
                except AttributeError:
                    try:
                        profile_dict = profile.dict()
                    except AttributeError:
                        profile_dict = profile.__dict__
                profile_ref.set(profile_dict)
            else:
                profile_ref.update(profile_data)

            return await self.get_user_profile(uid)

        except Exception as e:
            raise Exception(f"Error updating user profile: {str(e)}")

    # ============================================
    # CHAT OPERATIONS
    # ============================================

    async def create_chat_session(self, user_id: str, session_id: str):
        """Creates a new chat session in Firestore"""
        session_ref = self.db.collection("chat_sessions").document(session_id)
        session_ref.set(
            {
                "sessionId": session_id,
                "userId": user_id,
                "createdAt": datetime.now(timezone.utc),
                "lastMessageAt": datetime.now(timezone.utc),
            }
        )

    async def add_chat_message(self, session_id: str, message: ChatMessage):
        """Adds a chat message to a session's subcollection in Firestore"""
        message_dict = message.model_dump(by_alias=True)
        if isinstance(message_dict.get("createdAt"), str):
            message_dict["createdAt"] = datetime.fromisoformat(message_dict["createdAt"])
        elif message_dict.get("createdAt") is None:
            message_dict["createdAt"] = datetime.now(timezone.utc)

        message_id = (
            message.id
            if message.id
            else self.db.collection("chat_sessions")
            .document(session_id)
            .collection("messages")
            .document()
            .id
        )
        message_dict["id"] = message_id

        self.db.collection("chat_sessions").document(session_id).collection(
            "messages"
        ).document(message_id).set(message_dict)

        self.db.collection("chat_sessions").document(session_id).update(
            {"lastMessageAt": datetime.now(timezone.utc)}
        )

    async def get_chat_history(self, session_id: str) -> List[ChatMessage]:
        """Retrieves chat history for a given session from Firestore"""
        messages_ref = (
            self.db.collection("chat_sessions")
            .document(session_id)
            .collection("messages")
        )
        query = messages_ref.order_by("createdAt").stream()

        messages = []
        for doc in query:
            message_data = doc.to_dict()
            if "id" not in message_data:
                message_data["id"] = doc.id
            messages.append(ChatMessage(**message_data))
        return messages

    async def delete_chat_session(self, session_id: str):
        """Deletes a chat session and all its messages from Firestore"""
        session_ref = self.db.collection("chat_sessions").document(session_id)
        messages_ref = session_ref.collection("messages")
        snapshot = messages_ref.stream()
        for doc in snapshot:
            doc.reference.delete()
        session_ref.delete()

    # ============================================
    # STORAGE HELPERS
    # ============================================

    async def upload_file(self, path: str, content: bytes, content_type: str) -> str:
        """Upload bytes to Firebase Storage and return a usable URL"""
        try:
            from firebase_admin import storage as fb_storage

            def _upload():
                bucket = fb_storage.bucket()
                blob = bucket.blob(path)
                blob.upload_from_string(content, content_type=content_type)
                try:
                    blob.make_public()
                    return blob.public_url
                except Exception:
                    try:
                        url = blob.generate_signed_url(expiration=timedelta(hours=1))
                        return url
                    except Exception:
                        return f"gs://{bucket.name}/{path}"

            return await __import__("asyncio").to_thread(_upload)
        except Exception as e:
            raise Exception(f"Storage upload failed: {str(e)}")

    # ============================================
    # ARTICLE OPERATIONS
    # ============================================
    async def get_all_articles(self) -> List["Article"]:
        """Fetches all articles from the 'articles' Firestore collection"""
        from app.models.article import firestore_article_to_model

        articles_ref = self.db.collection("articles")
        docs = articles_ref.stream()

        articles = []
        for doc in docs:
            articles.append(firestore_article_to_model(doc.to_dict(), doc.id))
        return articles


# Global Firebase service instance
firebase_service = FirebaseService()
