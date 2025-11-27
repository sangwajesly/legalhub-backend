from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class CreateSessionResponse(BaseModel):
    sessionId: str


class MessageRequest(BaseModel):
    sessionId: Optional[str]
    message: str


class MessageResponse(BaseModel):
    reply: str
    sessionId: str


class ChatMessage(BaseModel):
    id: Optional[str]
    role: str
    text: str
    userId: Optional[str]
    createdAt: Optional[datetime]


class HistoryResponse(BaseModel):
    messages: List[ChatMessage]


class FeedbackRequest(BaseModel):
    sessionId: str
    messageId: str
    rating: int = 0
