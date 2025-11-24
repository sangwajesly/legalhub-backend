from fastapi import Depends, HTTPException, status, Header
from typing import Optional

from app.services import auth_service


async def get_current_user(authorization: Optional[str] = Header(None)):
    # For testing purposes, return a dummy user
    return {"uid": "test_user_id", "email": "test@example.com"}
