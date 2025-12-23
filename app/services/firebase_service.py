"""
Firebase service for Firestore and Authentication operations
"""

from __future__ import annotations
import json  # Import json for parsing credentials
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC, timedelta
import os
import json


from app.config import settings
from app.models.user import (
    User,
    UserProfile,
    # Assuming these models are Pydantic or have a .model_dump() / .dict() method
)
from app.models.user import user_model_to_firestore
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

    # Firestore handles datetime objects directly, but ensure they are included
    # We should also ensure the 'uid' is correctly named if it was defined as 'id' in the Pydantic model

    # Example conversion for Pydantic models with datetime fields:
    if "created_at" in user_dict and isinstance(user_dict["created_at"], datetime):
        # Firestore SDK handles datetime objects, so this is usually fine
        pass

    if "updated_at" in user_dict and isinstance(user_dict["updated_at"], datetime):
        # Firestore SDK handles datetime objects, so this is usually fine
        pass

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
                print(
                    f"Firebase initialized with emulator: {settings.FIREBASE_EMULATOR_HOST}"
                )
            else:
                # Use production credentials
                if settings.FIREBASE_CREDENTIALS_JSON:
                    try:
                        cred_dict = json.loads(
                            settings.FIREBASE_CREDENTIALS_JSON)
                        cred = credentials.Certificate(cred_dict)
                        print(
                            "Firebase initialized with credentials from FIREBASE_CREDENTIALS_JSON")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing FIREBASE_CREDENTIALS_JSON: {e}")
                        raise
                else:
                    # Fallback to file path
                    cred = credentials.Certificate(
                        settings.FIREBASE_CREDENTIALS_PATH)
                    print(
                        f"Firebase initialized with credentials from {settings.FIREBASE_CREDENTIALS_PATH}")

                firebase_admin.initialize_app(
                    cred, {"storageBucket": settings.FIREBASE_STORAGE_BUCKET}
                )
            print("Firebase Admin SDK initialization successful.")
        except Exception as e:
            # Explicit error logging
            print(f"ERROR: Firebase Admin SDK initialization failed: {e}")
            raise  # Re-raise to prevent the app from running with a broken Firebase setup
    # ============================================

    async def create_user(
        self,
        email: str,
        password: Optional[str] = None,  # Make password optional
        display_name: str = None,
        role: str = "user",
        phone_number: Optional[str] = None,
        email_verified: bool = False,  # Add email_verified
        photo_url: Optional[str] = None,  # Add photo_url
        is_new_user: bool = True,  # Flag to indicate if user is truly new to Firebase Auth
    ) -> User:
        """
        Create a new user in Firebase Authentication (if new) and Firestore

        Args:
            email: User's email
            password: User's password (optional, if user already exists in Firebase Auth)
            display_name: User's display name
            role: User's role (default: "user")
            phone_number: Optional phone number
            email_verified: Whether the email is verified
            photo_url: Optional photo URL
            is_new_user: If True, creates user in Firebase Auth. If False, assumes user exists.

        Returns:
            User object
        """
        try:
            uid = None
            if is_new_user and password:
                # Create user in Firebase Authentication only if truly new and password provided
                firebase_user = firebase_auth.create_user(
                    email=email,
                    password=password,
                    display_name=display_name,
                    phone_number=phone_number,
                    email_verified=email_verified,
                    photo_url=photo_url
                )
                uid = firebase_user.uid
            elif not is_new_user:
                # If not a new user, assume they exist in Firebase Auth and get their UID
                # This path is typically for social logins where Firebase Auth handles creation
                try:
                    firebase_user = firebase_auth.get_user_by_email(email)
                    uid = firebase_user.uid
                except firebase_auth.UserNotFoundError:
                    # If user is marked as not new, but not found in Firebase Auth,
                    # this is an inconsistency, raise an error or attempt to create without password
                    if password:  # If password is provided, try creating
                        firebase_user = firebase_auth.create_user(
                            email=email,
                            password=password,
                            display_name=display_name,
                            phone_number=phone_number,
                            email_verified=email_verified,
                            photo_url=photo_url
                        )
                        uid = firebase_user.uid
                    else:
                        raise ValueError(f"User with email {email} not found in Firebase Auth "
                                         "and no password provided for creation.")
            else:  # is_new_user is True but no password - invalid state for create_user
                raise ValueError(
                    "Password must be provided for new user registration.")

            # Create user document in Firestore using the Pydantic model for structure
            user = User(
                uid=uid,
                email=email,
                display_name=display_name,
                role=role,
                phone_number=phone_number,
                email_verified=email_verified,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                profile_picture=photo_url,
            )

            # Save to Firestore using the canonical camelCase mapping.
            firestore_data = user_model_to_firestore(user)

            import asyncio  # Ensure asyncio is imported

            try:
                await asyncio.to_thread(self.db.collection("users").document(uid).set, firestore_data)
            except Exception as firestore_e:
                print(
                    f"DEBUG: Failed to save user {uid} to Firestore: {firestore_e}")
                raise Exception(
                    f"Error saving user to Firestore: {firestore_e}")

            return user

        except firebase_auth.EmailAlreadyExistsError:
            raise ValueError("Email already exists")
        except Exception as e:
            # Log the specific error for better debugging
            print(
                f"DEBUG: Failed to create user or save to Firestore: {str(e)}")
            raise Exception(f"Error creating user: {str(e)}")

    async def get_user_by_uid(self, uid: str) -> Optional[User]:
        """
        Get user by UID from Firestore with robust fallback.
        Priority: 'users' -> 'user_profiles' -> Firebase Auth (create if missing)
        """
        try:
            import asyncio

            # Phase 1: Check 'users' collection (Standard Email/Password Users)
            # ----------------------------------------------------------------
            users_ref = self.db.collection("users").document(uid)
            doc = await asyncio.to_thread(users_ref.get)

            if doc.exists:
                try:
                    doc_data = doc.to_dict()
                    doc_data["uid"] = uid
                    # Validating existing users should generally pass, but let's be safe
                    return User.model_validate(doc_data)
                except Exception as e:
                    print(
                        f"WARNING: Validation failed for user in 'users' {uid}: {e}. Returning manual object.")
                    return self._construct_safe_user(uid, doc.to_dict())

            # Phase 2: Check 'user_profiles' collection (Social/Google Users)
            # ---------------------------------------------------------------
            profiles_ref = self.db.collection("user_profiles").document(uid)
            profile_doc = await asyncio.to_thread(profiles_ref.get)

            if profile_doc.exists:
                data = profile_doc.to_dict()
                data["uid"] = uid

                # If critical fields are missing, fetch from Auth to backfill
                if not data.get("email") or not data.get("role") or not data.get("displayName"):
                    try:
                        firebase_user = await asyncio.to_thread(firebase_auth.get_user, uid)
                        if not data.get("email"):
                            data["email"] = firebase_user.email
                        if not data.get("displayName"):
                            data["displayName"] = firebase_user.display_name
                        if not data.get("profilePicture"):
                            data["profilePicture"] = firebase_user.photo_url
                        if "emailVerified" not in data:
                            data["emailVerified"] = firebase_user.email_verified
                    except Exception as auth_fetch_err:
                        print(
                            f"DEBUG: Could not backfill from Auth for {uid}: {auth_fetch_err}")

                # Apply hard defaults for anything still missing
                if not data.get("email"):
                    data["email"] = f"{uid}@unknown.com"
                if not data.get("role"):
                    data["role"] = "user"
                if not data.get("displayName"):
                    data["displayName"] = "User"

                try:
                    return User.model_validate(data)
                except Exception as val_error:
                    print(
                        f"DEBUG: Validation failed for profile {uid}: {val_error}. Returning manual object.")
                    return self._construct_safe_user(uid, data)

            # Phase 3: Fallback - Create from Firebase Auth
            # ---------------------------------------------
            # This handles new social users who have a token but no Firestore doc yet
            try:
                firebase_user = await asyncio.to_thread(firebase_auth.get_user, uid)
                print(
                    f"DEBUG: User {uid} found in Auth but missing in Firestore. Creating new record...")

                new_user = User(
                    uid=uid,
                    email=firebase_user.email,
                    display_name=firebase_user.display_name or "User",
                    role="user",
                    photo_url=firebase_user.photo_url,
                    email_verified=firebase_user.email_verified,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )

                # Check if we should save to users or user_profiles?
                # For safety/legacy compatibility, we save simple records to 'users'
                # unless we know it's a social login, but here we just want them to work.
                await asyncio.to_thread(users_ref.set, user_model_to_firestore(new_user))
                return new_user

            except Exception as auth_e:
                print(f"DEBUG: User {uid} not found in Auth either: {auth_e}")
                return None

        except Exception as e:
            print(f"ERROR: Critical failure in get_user_by_uid({uid}): {e}")
            import traceback
            traceback.print_exc()
            return None

    def _construct_safe_user(self, uid: str, data: Dict[str, Any]) -> User:
        """Helper to manually construct a User object ignoring validation strictness"""
        return User(
            uid=uid,
            email=data.get("email") or f"{uid}@unknown.com",
            display_name=data.get("displayName") or data.get(
                "display_name") or "User",
            role=data.get("role") or "user",
            email_verified=data.get("emailVerified") or False,
            is_active=data.get("isActive", True),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            profile_picture=data.get(
                "profilePicture") or data.get("profile_picture")
        )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email from Firestore.
        Uses stream() but wraps it to prevent blocking the event loop.
        """
        try:
            import asyncio
            users_ref = self.db.collection("users")
            query = users_ref.where("email", "==", email).limit(1)

            # Properly await the blocking stream call
            # stream() returns a generator, so we iterate it in the thread
            def get_single_doc():
                docs = list(query.stream())
                if docs:
                    return docs[0]
                return None

            doc = await asyncio.to_thread(get_single_doc)

            if doc:
                doc_data = doc.to_dict()
                doc_data["uid"] = doc.id
                return User.model_validate(doc_data)

            return None
        except Exception as e:
            raise Exception(f"Error getting user by email: {str(e)}")

    async def update_user(self, uid: str, data: Dict[str, Any]) -> User:
        """
        Update user information in Firestore

        Args:
            uid: User's unique identifier
            data: Dictionary of fields to update

        Returns:
            Updated User object
        """
        try:
            # Normalize incoming keys to the canonical Firestore schema (camelCase).
            # We accept both snake_case and camelCase inputs to avoid breaking callers.
            normalized: Dict[str, Any] = {}

            key_map = {
                "display_name": "displayName",
                "displayName": "displayName",
                "email_verified": "emailVerified",
                "emailVerified": "emailVerified",
                "phone_number": "phoneNumber",
                "phoneNumber": "phoneNumber",
                "profile_picture": "profilePicture",
                "profilePicture": "profilePicture",
                "is_active": "isActive",
                "isActive": "isActive",
                "is_deleted": "isDeleted",
                "isDeleted": "isDeleted",
                "last_login": "lastLogin",
                "lastLogin": "lastLogin",
                "role": "role",
                "email": "email",
            }

            for k, v in (data or {}).items():
                mapped = key_map.get(k)
                if mapped:
                    normalized[mapped] = v
                else:
                    # Preserve unknown fields as-is (e.g. future expansion).
                    normalized[k] = v

            # Always set canonical updatedAt timestamp
            normalized["updatedAt"] = datetime.now(UTC)

            # Update Firestore
            user_ref = self.db.collection("users").document(uid)
            await asyncio.to_thread(user_ref.update, normalized)

            # Also update Firebase Auth if display name changed
            if "displayName" in normalized:
                await asyncio.to_thread(firebase_auth.update_user, uid, display_name=normalized["displayName"])

            # Get and return updated user
            return await self.get_user_by_uid(uid)

        except Exception as e:
            raise Exception(f"Error updating user: {str(e)}")

    async def delete_user(self, uid: str) -> bool:
        """
        Delete user from Firebase Authentication and Firestore

        Args:
            uid: User's unique identifier

        Returns:
            True if successful
        """
        try:
            # Delete from Firebase Authentication
            await asyncio.to_thread(firebase_auth.delete_user, uid)

            # Delete from Firestore
            await asyncio.to_thread(self.db.collection("users").document(uid).delete)

            return True
        except Exception as e:
            raise Exception(f"Error deleting user: {str(e)}")

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token

        Args:
            id_token: Firebase ID token to verify

        Returns:
            Decoded token claims
        """
        try:
            import asyncio  # Ensure asyncio is imported
            decoded_token = await asyncio.to_thread(firebase_auth.verify_id_token, id_token)
            return decoded_token
        except Exception as e:
            raise Exception(f"Invalid token: {str(e)}")

    # ============================================
    # USER PROFILE OPERATIONS
    # ============================================

    async def get_user_profile(self, uid: str) -> Optional[UserProfile]:
        """
        Get user profile from Firestore

        Args:
            uid: User's unique identifier

        Returns:
            UserProfile object or None if not found
        """
        try:
            import asyncio  # Ensure asyncio is imported
            doc = await asyncio.to_thread(self.db.collection("user_profiles").document(uid).get)
            if doc.exists:
                doc_data = doc.to_dict()
                doc_data["uid"] = uid  # Ensure uid is set
                return UserProfile.model_validate(doc_data)
            return None
        except Exception as e:
            raise Exception(f"Error getting user profile: {str(e)}")

    async def update_user_profile(
        self, uid: str, profile_data: Dict[str, Any]
    ) -> UserProfile:
        """
        Update or create user profile

        Args:
            uid: User's unique identifier
            profile_data: Profile data to update

        Returns:
            Updated UserProfile object
        """
        try:
            import asyncio  # Ensure asyncio is imported
            profile_ref = self.db.collection("user_profiles").document(uid)

            # Check if profile exists
            doc = await asyncio.to_thread(profile_ref.get)
            if not doc.exists:
                # Create new profile
                profile = UserProfile(uid=uid, **profile_data)

                try:
                    profile_dict = profile.model_dump()
                except AttributeError:
                    try:
                        profile_dict = profile.dict()
                    except AttributeError:
                        profile_dict = profile.__dict__

                await asyncio.to_thread(profile_ref.set, profile_dict)
            else:
                # Update existing profile
                await asyncio.to_thread(profile_ref.update, profile_data)

            return await self.get_user_profile(uid)

        except Exception as e:
            raise Exception(f"Error updating user profile: {str(e)}")

    # ============================================
    # CHAT OPERATIONS
    # ============================================

    async def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single chat session by its ID from Firestore.
        """
        import asyncio
        session_ref = self.db.collection("chat_sessions").document(session_id)
        doc = await asyncio.to_thread(session_ref.get)
        if doc.exists:
            return {**doc.to_dict(), "sessionId": doc.id}
        return None

    async def create_chat_session(self, user_id: str, session_id: str):
        """
        Creates a new chat session in Firestore.
        """
        import asyncio  # Ensure asyncio is imported
        session_ref = self.db.collection("chat_sessions").document(session_id)
        await asyncio.to_thread(session_ref.set,
                                {
                                    "sessionId": session_id,
                                    "userId": user_id,
                                    "createdAt": datetime.now(UTC),
                                    "lastMessageAt": datetime.now(UTC),
                                }
                                )

    async def get_user_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all chat sessions for a specific user, ordered by lastMessageAt desc.
        """
        try:
            import asyncio  # Ensure asyncio is imported
            sessions_ref = self.db.collection("chat_sessions")
            # Note: This query requires a composite index on [userId, lastMessageAt DESC]
            # If failing, check Firebase console indexes.
            query = (
                sessions_ref.where("userId", "==", user_id)
                .order_by("lastMessageAt", direction=firestore.Query.DESCENDING)
            )

            sessions = []
            for doc in await asyncio.to_thread(query.stream):
                data = doc.to_dict()
                # Ensure sessionId is present (it should be, but good to be safe)
                if "sessionId" not in data:
                    data["sessionId"] = doc.id
                sessions.append(data)
            return sessions

        except Exception as e:
            # Fallback if index is missing: try without ordering first, or handle gracefully
            print(f"DEBUG: Failed to query sessions with order: {e}")
            try:
                # Retry without ordering (might be slower or unsorted, but works without index)
                query = sessions_ref.where("userId", "==", user_id)
                sessions = []
                for doc in await asyncio.to_thread(query.stream):
                    data = doc.to_dict()
                    if "sessionId" not in data:
                        data["sessionId"] = doc.id
                    sessions.append(data)

                # Sort in memory
                sessions.sort(
                    key=lambda x: x.get("lastMessageAt", datetime.min), reverse=True
                )
                return sessions
            except Exception as e2:
                print(f"Error getting user sessions: {e2}")
                return []

    async def add_chat_message(self, session_id: str, message: ChatMessage):
        """
        Adds a chat message to a session's subcollection in Firestore.
        """
        import asyncio  # Ensure asyncio is imported
        message_dict = message.model_dump(by_alias=True)
        # Ensure createdAt is a datetime object for Firestore
        if isinstance(message_dict.get("createdAt"), str):
            message_dict["createdAt"] = datetime.fromisoformat(
                message_dict["createdAt"]
            )
        elif message_dict.get("createdAt") is None:
            message_dict["createdAt"] = datetime.now(UTC)

        # Add a unique ID for the message document
        if not message.id:
            # document().id is a synchronous operation on the Client/CollectionReference
            message_id = (
                self.db.collection("chat_sessions")
                .document(session_id)
                .collection("messages")
                .document()
                .id
            )
        else:
            message_id = message.id
        # Ensure the ID is part of the stored document
        message_dict["id"] = message_id

        await asyncio.to_thread(self.db.collection("chat_sessions").document(session_id).collection(
            "messages"
        ).document(message_id).set, message_dict)

        # Update lastMessageAt for the session
        await asyncio.to_thread(self.db.collection("chat_sessions").document(session_id).update,
                                {"lastMessageAt": datetime.now(UTC)}
                                )

    async def get_chat_history(self, session_id: str) -> List[ChatMessage]:
        """
        Retrieves chat history for a given session from Firestore.
        """
        import asyncio  # Ensure asyncio is imported
        messages_ref = (
            self.db.collection("chat_sessions")
            .document(session_id)
            .collection("messages")
        )
        query = messages_ref.order_by("createdAt")

        messages = []
        for doc in await asyncio.to_thread(query.stream):
            message_data = doc.to_dict()
            # Ensure 'id' field is set from document ID if not present in data
            if "id" not in message_data:
                message_data["id"] = doc.id
            messages.append(ChatMessage(**message_data))
        return messages

    async def delete_chat_session(self, session_id: str):
        """
        Deletes a chat session and all its messages from Firestore.
        """
        import asyncio  # Ensure asyncio is imported
        session_ref = self.db.collection("chat_sessions").document(session_id)

        # Delete all messages in the subcollection
        messages_ref = session_ref.collection("messages")
        snapshot = await asyncio.to_thread(messages_ref.stream)
        for doc in snapshot:
            await asyncio.to_thread(doc.reference.delete)

        # Delete the session document itself
        await asyncio.to_thread(session_ref.delete)

    # ============================================
    # DIRECT MESSAGING OPERATIONS
    # ============================================

    async def add_direct_message(self, message: "DirectMessage"):
        """
        Adds a direct message to the 'direct_messages' collection.
        Messages are stored in a top-level collection for simplicity in MVP.
        """
        import asyncio  # Ensure asyncio is imported
        msg_dict = message.model_dump(by_alias=True)
        if isinstance(msg_dict.get("timestamp"), str):
            msg_dict["timestamp"] = datetime.fromisoformat(
                msg_dict["timestamp"])

        # Use provided ID or generate one
        if not message.id:
            ref = await asyncio.to_thread(self.db.collection("direct_messages").document)
            message.id = ref.id
            msg_dict["id"] = ref.id
        else:
            ref = self.db.collection("direct_messages").document(message.id)

        await asyncio.to_thread(ref.set, msg_dict)
        return message

    async def get_direct_messages(self, user1_id: str, user2_id: str, limit: int = 50) -> List["DirectMessage"]:
        """
        Get messages between two users (bidirectional).
        Requires a composite index on [senderId, receiverId, timestamp] AND [receiverId, senderId, timestamp]
        OR we query twice and merge (simpler for MVP without custom indexes).
        """
        from app.models.communication import DirectMessage
        import asyncio  # Ensure asyncio is imported

        # Query 1: user1 -> user2
        q1 = (
            self.db.collection("direct_messages")
            .where("senderId", "==", user1_id)
            .where("receiverId", "==", user2_id)
        )

        # Query 2: user2 -> user1
        q2 = (
            self.db.collection("direct_messages")
            .where("senderId", "==", user2_id)
            .where("receiverId", "==", user1_id)
        )

        msgs = []
        for d in await asyncio.to_thread(q1.stream):
            msgs.append(DirectMessage(**d.to_dict()))
        for d in await asyncio.to_thread(q2.stream):
            msgs.append(DirectMessage(**d.to_dict()))

        # Sort by timestamp
        msgs.sort(key=lambda x: x.timestamp)
        return msgs

    # ============================================
    # STORAGE HELPERS
    # ============================================

    async def upload_file(self, path: str, content: bytes, content_type: str) -> str:
        """Upload bytes to Firebase Storage and return a usable URL.

        Tries to make the object public and return `public_url`. If signing is
        available will attempt to generate a signed URL, otherwise returns a
        gs:// path as a fallback.
        """
        try:
            # import here to avoid module-level dependency at import time
            from firebase_admin import storage as fb_storage
            import asyncio  # Required for asyncio.to_thread

            def _upload():
                bucket = fb_storage.bucket()
                blob = bucket.blob(path)
                # upload_from_string accepts bytes
                blob.upload_from_string(content, content_type=content_type)
                try:
                    blob.make_public()
                    return blob.public_url
                except Exception:
                    try:
                        # Try signed url (may require google-cloud-storage credentials)
                        url = blob.generate_signed_url(
                            expiration=timedelta(hours=1))
                        return url
                    except Exception:
                        return f"gs://{bucket.name}/{path}"

            # Run blocking upload in a thread to avoid blocking the event loop
            return await asyncio.to_thread(_upload)
        except Exception as e:
            # bubble up or return a fallback
            raise Exception(f"Storage upload failed: {str(e)}")

    # ============================================
    # ARTICLE OPERATIONS
    # ============================================
    async def get_all_articles(self) -> List["Article"]:
        """
        Fetches all articles from the 'articles' Firestore collection.
        """
        from app.models.article import firestore_article_to_model
        import asyncio  # Ensure asyncio is imported

        articles_ref = self.db.collection("articles")
        docs = await asyncio.to_thread(articles_ref.stream)

        articles = []
        for doc in docs:
            articles.append(firestore_article_to_model(doc.to_dict(), doc.id))
        return articles

    async def add_bookmark(self, uid: str, article_id: str) -> bool:
        """
        Adds an article to a user's bookmarks.
        """
        try:
            import asyncio  # Ensure asyncio is imported
            bm_ref = self.db.collection("users").document(
                uid).collection("bookmarks").document(article_id)
            await asyncio.to_thread(bm_ref.set, {"articleId": article_id, "createdAt": datetime.now(UTC)})
            return True
        except Exception as e:
            print(f"Error adding bookmark: {e}")
            return False

    async def remove_bookmark(self, uid: str, article_id: str) -> bool:
        """
        Removes an article from a user's bookmarks.
        """
        try:
            import asyncio  # Ensure asyncio is imported
            bm_ref = self.db.collection("users").document(
                uid).collection("bookmarks").document(article_id)
            await asyncio.to_thread(bm_ref.delete)
            return True
        except Exception as e:
            print(f"Error removing bookmark: {e}")
            return False

    async def get_bookmark(self, uid: str, article_id: str) -> bool:
        """
        Checks if an article is bookmarked by a user.
        """
        try:
            import asyncio  # Ensure asyncio is imported
            bm_ref = self.db.collection("users").document(
                uid).collection("bookmarks").document(article_id)
            return (await asyncio.to_thread(bm_ref.get)).exists
        except Exception as e:
            print(f"Error checking bookmark: {e}")
            return False

    # ============================================
    # GENERIC QUERY OPERATIONS
    # ============================================
    async def query_collection(
        self,
        collection_name: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        direction: str = firestore.Query.ASCENDING,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        start_after_doc_id: Optional[str] = None,
        get_total_count: bool = False
    ) -> tuple[List[tuple[str, Dict[str, Any]]], int]:
        """
        Queries a Firestore collection with filters, ordering, and pagination.

        Args:
            collection_name: The name of the Firestore collection.
            filters: A list of tuples, each representing a filter condition (field, op, value).
                     e.g., [("status", "==", "active"), ("created_at", ">", some_datetime)]
            order_by: The field to order the results by.
            direction: The order direction ('ASCENDING' or 'DESCENDING').
            limit: The maximum number of documents to return.
            offset: The number of documents to skip. (Less efficient for Firestore)
            start_after_doc_id: The ID of the document to start fetching results after (for cursor-based pagination).
            get_total_count: If True, also returns the total count of documents matching the filters (without limit/offset).

        Returns:
            A tuple containing:
            - A list of tuples, where each tuple is (document_id, document_data).
            - The total count of documents matching the filters (or 0 if get_total_count is False).
        """
        import asyncio  # Ensure asyncio is imported

        collection_ref = self.db.collection(collection_name)
        query = collection_ref

        # Apply filters
        if filters:
            # For backward compatibility and developer convenience,
            # allow dictionary of {field: value} which defaults to '==' comparison.
            if isinstance(filters, dict):
                normalized_filters = []
                for k, v in filters.items():
                    normalized_filters.append((k, "==", v))
                filters = normalized_filters

            for f in filters:
                if len(f) == 3:
                    query = query.where(f[0], f[1], f[2])
                else:
                    raise ValueError(
                        f"Invalid filter format: {f}. Expected (field, op, value)")

        # Function to execute synchronous Firestore stream in a thread
        def _get_stream_data(q):
            return [(doc.id, doc.to_dict()) for doc in q.stream()]

        total_count = 0
        if get_total_count:
            # For simplicity, streaming all documents to get count.
            # For very large collections, consider maintaining a separate counter or using Cloud Functions.
            all_docs_for_count = await asyncio.to_thread(_get_stream_data, query)
            total_count = len(all_docs_for_count)

        # Apply ordering
        if order_by:
            query = query.order_by(order_by, direction=direction)

        # Apply start_after for cursor-based pagination
        if start_after_doc_id:
            def _get_doc_sync(col_ref, doc_id):
                return col_ref.document(doc_id).get()

            start_after_doc = await asyncio.to_thread(_get_doc_sync, collection_ref, start_after_doc_id)
            if start_after_doc.exists:
                query = query.start_after(start_after_doc)
            # If doc does not exist, the query will proceed as if start_after was not applied.

        # Apply offset (less efficient than start_after for large datasets)
        if offset is not None and offset > 0:
            query = query.offset(offset)

        # Apply limit
        if limit:
            query = query.limit(limit)

        # Execute the final query in a thread
        docs = await asyncio.to_thread(_get_stream_data, query)

        return docs, total_count


# Global Firebase service instance
firebase_service = FirebaseService()
