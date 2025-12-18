from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


from pydantic import BaseModel, Field, ConfigDict


class ChatMessage(BaseModel):
    id: Optional[str] = Field(None, alias="id")
    role: str
    text: str
    user_id: Optional[str] = Field(None, alias="userId")
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ChatSession(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    user_id: Optional[str] = Field(None, alias="userId")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    last_message_at: Optional[datetime] = Field(None, alias="lastMessageAt")

    model_config = ConfigDict(populate_by_name=True)
