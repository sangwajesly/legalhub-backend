from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


class DirectMessage(BaseModel):
    id: Optional[str] = None
    sender_id: str = Field(..., alias="senderId")
    receiver_id: str = Field(..., alias="receiverId")
    content: str
    timestamp: datetime
    read: bool = False
    booking_id: Optional[str] = Field(None, alias="bookingId")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "msg_123",
                "senderId": "user_abc",
                "receiverId": "lawyer_xyz",
                "content": "Hello, I have a question about our appointment.",
                "timestamp": "2024-01-20T10:00:00Z",
                "read": False,
                "bookingId": "booking_456"
            }
        }
    )


class Conversation(BaseModel):
    """
    Represents a conversation summary between two users.
    Computed client-side or backend-side for listing 'Chats'.
    """
    other_user_id: str = Field(..., alias="otherUserId")
    last_message: DirectMessage = Field(..., alias="lastMessage")
    unread_count: int = Field(0, alias="unreadCount")

    model_config = ConfigDict(populate_by_name=True)


class MessageCreate(BaseModel):
    receiver_id: str = Field(..., alias="receiverId")
    content: str
    booking_id: Optional[str] = Field(None, alias="bookingId")

    model_config = ConfigDict(populate_by_name=True)
