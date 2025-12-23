import asyncio
import uuid
from app.services import langchain_service


async def test_stateless_chat():
    print("--- Running Totally Stateless Test (No DB Session) ---")

    # 1. Use a non-existent session ID
    user_id = "test_user_stateless"
    session_id = str(uuid.uuid4())
    print(f"Using random session_id: {session_id} (Not in DB)")

    # 2. Define history
    history = [
        {"role": "user", "text": "Who is the CEO of Google?"},
        {"role": "assistant",
            "text": "The CEO of Google (and Alphabet) is Sundar Pichai."}
    ]

    # 3. Ask a follow-up question
    message = "When was he born?"
    print(f"User: {message}")

    try:
        reply = await langchain_service.generate_response(
            session_id=session_id,
            user_id=user_id,
            user_message=message,
            history=history
        )
        print(f"Assistant: {reply}")

        # Simple verification: Does it mention Sundar or 1972 or Pichai?
        if "Sundar" in reply or "1972" in reply or "Pichai" in reply:
            print("[SUCCESS] AI used provided history context without a DB session!")
        else:
            print("[WARNING] AI response might not have used context.")
            print(f"Response: {reply}")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
    finally:
        print("[OK] Test finished.")

if __name__ == "__main__":
    asyncio.run(test_stateless_chat())
