from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    id: Optional[str] = Field(None, alias="id")
    role: str
    text: str
    userId: Optional[str] = None
    createdAt: Optional[datetime] = None


class ChatSession(BaseModel):
    sessionId: str
    userId: Optional[str] = None
    createdAt: Optional[datetime] = None
    lastMessageAt: Optional[datetime] = None


