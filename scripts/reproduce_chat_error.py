import asyncio
import uuid
from datetime import datetime, UTC
from app.services import langchain_service
from app.models.user import User, UserRole


async def test_chat():
    print("Testing langchain_service.generate_response...")
    user = User(
        uid="test_user_id",
        email="test@example.com",
        display_name="Test User",
        role=UserRole.USER,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

    session_id = str(uuid.uuid4())

    try:
        reply = await langchain_service.generate_response(
            session_id=session_id,
            user_id=user.uid,
            user_message="Hello, can you help me with a legal question?",
            attachments=[]
        )
        print(f"Reply: {reply}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())
