"""
Local JSON Document Store & Auth Emulator for Offline Fallback
==============================================================
Provides local JSON file CRUD, subcollections, and query filtering that matches 
the Google Cloud Firestore client API, plus a mock implementation of Firebase Admin Auth.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Base directory for local JSON database records
LOCAL_DB_DIR = os.environ.get("LOCAL_DB_DIR", "./data/local_db")

# Regex to detect ISO-8601 datetime strings
ISO_DATETIME_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)


def _parse_iso_datetimes(data: Any) -> Any:
    """Recursively parses ISO-8601 datetime strings into timezone-aware datetimes."""
    if isinstance(data, dict):
        return {k: _parse_iso_datetimes(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_parse_iso_datetimes(item) for item in data]
    elif isinstance(data, str) and ISO_DATETIME_REGEX.match(data):
        try:
            val = data
            if val.endswith("Z"):
                val = val[:-1] + "+00:00"
            return datetime.fromisoformat(val)
        except Exception:
            return data
    return data


def _serialize_datetimes(data: Any) -> Any:
    """Recursively converts datetime objects to ISO strings for JSON serialization."""
    if isinstance(data, dict):
        return {k: _serialize_datetimes(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_datetimes(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    return data


class LocalDocumentSnapshot:
    """Firestore-compatible DocumentSnapshot mock"""

    def __init__(self, document_id: str, data: Optional[Dict[str, Any]]):
        self.id = document_id
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        return _parse_iso_datetimes(self._data) if self._data else None


class LocalDocumentReference:
    """Firestore-compatible DocumentReference mock"""

    def __init__(self, collection_path: str, document_id: str):
        self.collection_path = collection_path
        self.id = document_id
        self.file_path = os.path.join(
            LOCAL_DB_DIR, collection_path, f"{document_id}.json"
        )

    def collection(self, subcollection_name: str):
        """Returns a CollectionReference for a subcollection of this document"""
        sub_path = f"{self.collection_path}/{self.id}/{subcollection_name}"
        return LocalCollectionReference(sub_path)

    def get(self):
        if not os.path.exists(self.file_path):
            return LocalDocumentSnapshot(self.id, None)
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return LocalDocumentSnapshot(self.id, data)
        except Exception as e:
            logger.error(f"Error reading local document {self.file_path}: {e}")
            return LocalDocumentSnapshot(self.id, None)

    def set(self, data: Dict[str, Any], merge: bool = False):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        existing = {}
        if merge and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass

        serialized_data = _serialize_datetimes(data)
        updated = {**existing, **serialized_data}

        # Keep id in document if possible for convenience
        if "id" not in updated and "bookingId" not in updated and "caseId" not in updated:
            updated["id"] = self.id

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2)

    def update(self, data: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        existing = {}
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass

        serialized_data = _serialize_datetimes(data)
        updated = {**existing, **serialized_data}

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2)

    def delete(self):
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except Exception as e:
                logger.error(f"Error deleting local document {self.file_path}: {e}")


class LocalQuery:
    """Firestore-compatible Query mock with where, order_by, limit filters"""

    def __init__(self, collection_path: str, docs: List[LocalDocumentSnapshot]):
        self.collection_path = collection_path
        self._docs = docs

    def where(self, field: str, op: str, value: Any):
        filtered = []
        for doc in self._docs:
            data = doc.to_dict()
            if not data:
                continue

            # Resolve dotted path (e.g., "address.city")
            doc_val = data
            for part in field.split("."):
                if isinstance(doc_val, dict):
                    doc_val = doc_val.get(part)
                else:
                    doc_val = None
                    break

            match = False
            # Handle comparing datetimes to ISO strings or datetime objects
            if isinstance(doc_val, datetime) and isinstance(value, str):
                try:
                    value_dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    doc_val_cmp, value_cmp = doc_val.timestamp(), value_dt.timestamp()
                except Exception:
                    doc_val_cmp, value_cmp = doc_val, value
            else:
                doc_val_cmp, value_cmp = doc_val, value

            if op == "==":
                match = (doc_val_cmp == value_cmp)
            elif op == "!=":
                match = (doc_val_cmp != value_cmp)
            elif op == "<":
                match = (doc_val_cmp is not None and doc_val_cmp < value_cmp)
            elif op == "<=":
                match = (doc_val_cmp is not None and doc_val_cmp <= value_cmp)
            elif op == ">":
                match = (doc_val_cmp is not None and doc_val_cmp > value_cmp)
            elif op == ">=":
                match = (doc_val_cmp is not None and doc_val_cmp >= value_cmp)
            elif op == "in":
                match = (value is not None and doc_val_cmp in value)
            elif op == "not-in":
                match = (value is not None and doc_val_cmp not in value)
            elif op == "array-contains":
                match = (isinstance(doc_val, list) and value in doc_val)
            elif op == "array-contains-any":
                match = (isinstance(doc_val, list) and any(x in doc_val for x in value))

            if match:
                filtered.append(doc)

        return LocalQuery(self.collection_path, filtered)

    def order_by(self, field: str, direction: str = "ASCENDING"):
        def get_sort_key(doc):
            data = doc.to_dict() or {}
            val = data
            for part in field.split("."):
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    val = None
                    break
            if val is None:
                return "" if direction == "ASCENDING" else "\xff"
            if isinstance(val, datetime):
                return val.timestamp()
            return val

        reverse = (direction == "DESCENDING" or direction == "desc" or direction == -1)
        sorted_docs = sorted(self._docs, key=get_sort_key, reverse=reverse)
        return LocalQuery(self.collection_path, sorted_docs)

    def limit(self, count: int):
        return LocalQuery(self.collection_path, self._docs[:count])

    def stream(self) -> List[LocalDocumentSnapshot]:
        return self._docs


class LocalCollectionReference(LocalQuery):
    """Firestore-compatible CollectionReference mock"""

    def __init__(self, collection_path: str):
        self.collection_path = collection_path
        self.folder_path = os.path.join(LOCAL_DB_DIR, collection_path)

        docs = []
        if os.path.exists(self.folder_path):
            try:
                for entry in os.scandir(self.folder_path):
                    if entry.is_file() and entry.name.endswith(".json"):
                        doc_id = entry.name[:-5]
                        try:
                            with open(entry.path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            docs.append(LocalDocumentSnapshot(doc_id, data))
                        except Exception:
                            pass
            except Exception as e:
                logger.error(f"Error scanning local collection {self.folder_path}: {e}")

        super().__init__(collection_path, docs)

    def document(self, document_id: Optional[str] = None):
        if not document_id:
            document_id = str(uuid.uuid4())
        return LocalDocumentReference(self.collection_path, document_id)


class LocalFirestoreClient:
    """Mock for firestore.client() / google-cloud-firestore client"""

    class Query:
        ASCENDING = "ASCENDING"
        DESCENDING = "DESCENDING"

    def __init__(self):
        os.makedirs(LOCAL_DB_DIR, exist_ok=True)

    def collection(self, collection_name: str) -> LocalCollectionReference:
        return LocalCollectionReference(collection_name)


# ===========================================================================
# Firebase Authentication Mock layer
# ===========================================================================

class MockUserRecord:
    """Mock record returned by firebase_auth query methods"""

    def __init__(
        self,
        uid: str,
        email: str,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email_verified: bool = False,
        photo_url: Optional[str] = None,
    ):
        self.uid = uid
        self.email = email
        self.display_name = display_name
        self.phone_number = phone_number
        self.email_verified = email_verified
        self.photo_url = photo_url


class MockFirebaseAuth:
    """Mock representing the Firebase Admin Auth API methods"""

    class EmailAlreadyExistsError(Exception):
        pass

    class UserNotFoundError(Exception):
        pass

    @staticmethod
    def verify_id_token(id_token: str, *args, **kwargs) -> Dict[str, Any]:
        """Verify mock / local tokens or email strings directly for offline sessions"""
        if not id_token:
            raise ValueError("Token is empty")
        
        # If it is a local JWT, it might be verified by the backend. 
        # But if the proxy forwards it here, return the metadata.
        if id_token.count(".") == 2:
            raise ValueError("Token is an internal JWT access token, not a Firebase ID token")
            
        if id_token.startswith("mock_id_token_"):
            email = id_token[len("mock_id_token_"):]
            uid = email.replace("@", "_").replace(".", "_")
            return {"uid": uid, "email": email, "email_verified": True, "name": email.split("@")[0]}
        elif "@" in id_token:
            uid = id_token.replace("@", "_").replace(".", "_")
            return {"uid": uid, "email": id_token, "email_verified": True, "name": id_token.split("@")[0]}
        else:
            return {"uid": "mock_uid_123", "email": "mock_user@legalhub.com", "email_verified": True, "name": "Mock User"}

    @staticmethod
    def create_user(
        email: str,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email_verified: bool = False,
        photo_url: Optional[str] = None,
        uid: Optional[str] = None,
        *args,
        **kwargs,
    ) -> MockUserRecord:
        """Create mock user record and register it locally"""
        if not uid:
            uid = email.replace("@", "_").replace(".", "_")
        
        # Check if email exists
        try:
            MockFirebaseAuth.get_user_by_email(email)
            raise MockFirebaseAuth.EmailAlreadyExistsError("Email already exists")
        except MockFirebaseAuth.UserNotFoundError:
            pass

        record = MockUserRecord(
            uid=uid,
            email=email,
            display_name=display_name,
            phone_number=phone_number,
            email_verified=email_verified,
            photo_url=photo_url,
        )
        return record

    @staticmethod
    def get_user(uid: str, *args, **kwargs) -> MockUserRecord:
        """Get mock user record by UID from local JSON files"""
        file_path = os.path.join(LOCAL_DB_DIR, "users", f"{uid}.json")
        if not os.path.exists(file_path):
            file_path = os.path.join(LOCAL_DB_DIR, "user_profiles", f"{uid}.json")

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return MockUserRecord(
                    uid=uid,
                    email=data.get("email") or f"{uid}@unknown.com",
                    display_name=data.get("displayName") or data.get("display_name") or "User",
                    phone_number=data.get("phoneNumber") or data.get("phone_number"),
                    email_verified=data.get("emailVerified") or data.get("email_verified") or False,
                    photo_url=data.get("profilePicture") or data.get("profile_picture"),
                )
            except Exception:
                pass

        return MockUserRecord(
            uid=uid,
            email=f"{uid}@unknown.com",
            display_name="User",
            phone_number=None,
            email_verified=False,
            photo_url=None,
        )

    @staticmethod
    def get_user_by_email(email: str, *args, **kwargs) -> MockUserRecord:
        """Find user record by checking local JSON collection"""
        folder = os.path.join(LOCAL_DB_DIR, "users")
        if os.path.exists(folder):
            for name in os.listdir(folder):
                if name.endswith(".json"):
                    path = os.path.join(folder, name)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if data.get("email") == email:
                            uid = name[:-5]
                            return MockUserRecord(
                                uid=uid,
                                email=email,
                                display_name=data.get("displayName") or "User",
                                phone_number=data.get("phoneNumber"),
                                email_verified=data.get("emailVerified") or False,
                                photo_url=data.get("profilePicture"),
                            )
                    except Exception:
                        pass
        raise MockFirebaseAuth.UserNotFoundError(f"User with email {email} not found")

    @staticmethod
    def update_user(uid: str, **kwargs) -> MockUserRecord:
        """Update mock user metadata in local store"""
        file_path = os.path.join(LOCAL_DB_DIR, "users", f"{uid}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "display_name" in kwargs:
                    data["displayName"] = kwargs["display_name"]
                if "phone_number" in kwargs:
                    data["phoneNumber"] = kwargs["phone_number"]
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
        return MockFirebaseAuth.get_user(uid)

    @staticmethod
    def delete_user(uid: str, *args, **kwargs):
        """Mock deleting user"""
        pass
