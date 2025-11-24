from typing import Optional, Dict
import firebase_admin
from firebase_admin import auth as firebase_auth


def verify_id_token(id_token: str) -> Optional[Dict]:
    """Verify a Firebase ID token and return the decoded token (claims).

    Returns None if verification fails.
    """
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception:
        return None


def create_custom_token(uid: str) -> str:
    # Helper if you want to mint custom tokens for clients
    return firebase_auth.create_custom_token(uid).decode("utf-8")
