import os
from typing import Any, Dict, List, Optional
import uuid

import firebase_admin
from firebase_admin import credentials, firestore, storage

_app = None
_db = None
_bucket = None


def initialize_app(config) -> None:
    global _app, _db, _bucket
    if firebase_admin._apps:
        _app = firebase_admin.get_app()
    else:
        if getattr(config, "DEV_MODE", True) and not os.path.exists(
            config.FIREBASE_CREDENTIALS_PATH or ""
        ):
            # In DEV_MODE without credentials, skip initializing real Firebase.
            return
        cred_path = config.FIREBASE_CREDENTIALS_PATH
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _app = firebase_admin.initialize_app(cred, {
                "storageBucket": config.FIREBASE_STORAGE_BUCKET
            })
        else:
            # try default initialization
            _app = firebase_admin.initialize_app()

    try:
        _db = firestore.client()
    except Exception:
        _db = None

    try:
        _bucket = storage.bucket()
    except Exception:
        _bucket = None


def get_firestore():
    if _db is None:
        raise RuntimeError("Firestore client is not initialized")
    return _db


def create_user(uid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_firestore()
    doc_ref = db.collection("users").document(uid)
    doc_ref.set(data, merge=True)
    return {"uid": uid, **data}


def save_chat_session(user_id: Optional[str], session_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    db = get_firestore()
    if not session_id:
        session_id = str(uuid.uuid4())
    doc = db.collection("chat_sessions").document(session_id)
    payload = {"userId": user_id, "createdAt": firestore.SERVER_TIMESTAMP}
    payload.update(metadata or {})
    doc.set(payload)
    return {"sessionId": session_id, **payload}


def append_message(session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    db = get_firestore()
    messages_ref = db.collection("chat_sessions").document(session_id).collection("messages")
    doc = messages_ref.document()
    doc.set({**message, "createdAt": firestore.SERVER_TIMESTAMP})
    return {"id": doc.id, **message}


def get_chat_history(session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    db = get_firestore()
    messages_ref = db.collection("chat_sessions").document(session_id).collection("messages")
    docs = messages_ref.order_by("createdAt").limit(limit).stream()
    results = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        results.append(data)
    return results


def delete_chat_session(session_id: str) -> None:
    db = get_firestore()
    # Delete messages subcollection (Firestore doesn't cascade, so paginate)
    messages_ref = db.collection("chat_sessions").document(session_id).collection("messages")
    docs = messages_ref.stream()
    for d in docs:
        d.reference.delete()
    # Delete session document
    db.collection("chat_sessions").document(session_id).delete()
