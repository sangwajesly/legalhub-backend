"""
Firebase Model Context Protocol (MCP) Client.

This client wraps the FirebaseService and exposes methods that can be
registered with a conceptual Model Context Protocol (MCP) for broader
system integration.
"""

from app.services.firebase_service import FirebaseService
from app.models.user import User, UserProfile
from app.models.chat import ChatMessage
from typing import Optional, Dict, Any, List


class FirebaseMcpClient:
    """
    A client that exposes FirebaseService functionalities
    for integration into a Model Context Protocol (MCP).
    """

    def __init__(self, firebase_service: FirebaseService):
        self.firebase_service = firebase_service

    # User Operations
    async def create_user(
        self,
        email: str,
        password: str,
        display_name: str,
        role: str = "user",
        phone_number: Optional[str] = None,
    ) -> User:
        return await self.firebase_service.create_user(
            email,
            password,
            display_name,
            role,
            phone_number,
        )

    async def get_user_by_uid(self, uid: str) -> Optional[User]:
        return await self.firebase_service.get_user_by_uid(uid)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.firebase_service.get_user_by_email(email)

    async def update_user(self, uid: str, data: Dict[str, Any]) -> User:
        return await self.firebase_service.update_user(uid, data)

    async def delete_user(self, uid: str) -> bool:
        return await self.firebase_service.delete_user(uid)

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        return await self.firebase_service.verify_id_token(id_token)

    # User Profile Operations
    async def get_user_profile(self, uid: str) -> Optional[UserProfile]:
        return await self.firebase_service.get_user_profile(uid)

    async def update_user_profile(
        self, uid: str, profile_data: Dict[str, Any]
    ) -> UserProfile:
        return await self.firebase_service.update_user_profile(
            uid,
            profile_data,
        )

    # Chat Operations
    async def create_chat_session(self, user_id: str, session_id: str):
        return await self.firebase_service.create_chat_session(
            user_id,
            session_id,
        )

    async def add_chat_message(self, session_id: str, message: ChatMessage):
        return await self.firebase_service.add_chat_message(
            session_id,
            message,
        )

    async def get_chat_history(self, session_id: str) -> List[ChatMessage]:
        return await self.firebase_service.get_chat_history(session_id)

    async def delete_chat_session(self, session_id: str):
        return await self.firebase_service.delete_chat_session(session_id)

    # Storage Helpers
    async def upload_file(self, path: str, content: bytes, content_type: str) -> str:
        return await self.firebase_service.upload_file(
            path,
            content,
            content_type,
        )
