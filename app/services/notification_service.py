"""Notification service using Firebase Cloud Messaging (FCM)

This module provides a small async-friendly wrapper around firebase_admin.messaging
to send notifications to device tokens stored on user documents. It keeps imports
local to methods to avoid side-effects at import time.
"""

from typing import Optional, Dict, Any, List
import asyncio

from app.services.firebase_service import firebase_service


class NotificationService:
    """Thin wrapper to send FCM notifications."""

    async def send_to_token(
        self, token: str, title: str, body: str, data: Optional[Dict[str, str]] = None
    ) -> None:
        try:
            from firebase_admin import messaging

            message = messaging.Message(
                token=token,
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
            )
            # run blocking send in thread
            await asyncio.to_thread(messaging.send, message)
        except Exception:
            # best-effort; don't raise to avoid breaking core flows
            return

    async def send_to_tokens(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> None:
        if not tokens:
            return
        try:
            from firebase_admin import messaging

            # messaging.send_multicast accepts up to 500 tokens
            message = messaging.MulticastMessage(
                tokens=tokens,
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
            )
            await asyncio.to_thread(messaging.send_multicast, message)
        except Exception:
            return

    async def send_to_user(
        self, uid: str, title: str, body: str, data: Optional[Dict[str, str]] = None
    ) -> None:
        # Fetch user doc to locate FCM tokens (assumed stored as 'fcmTokens' list)
        try:
            doc = firebase_service.db.collection("users").document(uid).get()
            if not doc.exists:
                return
            user = doc.to_dict()
            tokens = user.get("fcmTokens") or user.get("fcm_tokens") or []
            if not tokens:
                return
            await self.send_to_tokens(tokens, title, body, data)
        except Exception:
            return


# single instance exported for app usage
notification_service = NotificationService()
