from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, UTC

from app.dependencies import get_current_user
from app.services import firebase_service
from app.models.communication import DirectMessage, MessageCreate
from app.models.user import User

router = APIRouter(prefix="/api/v1/communication", tags=["communication"])


@router.post("/messages", response_model=DirectMessage)
async def send_message(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Send a direct message to another user.
    """
    sender_id = current_user.uid

    # Validation: Ensure user exists? (Optional, but good practice)
    # receiver = await firebase_service.get_user_by_uid(payload.receiverId)
    # if not receiver: raise HTTPException(404, "Receiver not found")

    message = DirectMessage(
        senderId=sender_id,
        receiverId=payload.receiverId,
        content=payload.content,
        timestamp=datetime.now(UTC),
        bookingId=payload.bookingId,
        read=False
    )

    saved_msg = await firebase_service.add_direct_message(message)
    return saved_msg


@router.get("/messages/{other_user_id}", response_model=List[DirectMessage])
async def get_conversation(
    other_user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get message history with a specific user.
    """
    user_id = current_user.uid
    messages = await firebase_service.get_direct_messages(user_id, other_user_id)
    return messages
