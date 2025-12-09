from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class DirectMessage(BaseModel):
    id: Optional[str] = None
    senderId: str
    receiverId: str
    content: str
    timestamp: datetime
    read: bool = False
    bookingId: Optional[str] = None # Optional context: linked to a specific booking

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
    otherUserId: str
    lastMessage: DirectMessage
    unreadCount: int = 0

class MessageCreate(BaseModel):
    receiverId: str
    content: str
    bookingId: Optional[str] = None
