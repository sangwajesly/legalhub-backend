
from app.services import langchain_service
from app.services.firebase_service import firebase_service
import asyncio
import os
import sys
import uuid

# Ensure app is in path
sys.path.append(os.getcwd())


async def test_session_flow(user_id: str):
    print(f"--- Testing Session Flow for User {user_id} ---")

    session_id = str(uuid.uuid4())
    print(f"1. Creating Session {session_id}...")

    try:
        await langchain_service.create_session(user_id, session_id)
        print("[OK] Session creation call successful.")
    except Exception as e:
        print(f"[FAIL] Session creation failed: {e}")
        return

    print("\n2. Verifying in Firestore (get_chat_session)...")
    try:
        session = await firebase_service.get_chat_session(session_id)
        if session:
            print(f"[OK] Session found!")
            print(f"   Stored userId: {session.get('userId')}")
            print(f"   Expected userId: {user_id}")

            if session.get('userId') == user_id:
                print("[OK] User ID matches.")
            else:
                print("[FAIL] User ID MISMATCH.")
        else:
            print("[FAIL] Session NOT found in DB.")
    except Exception as e:
        print(f"[FAIL] Error getting session: {e}")

    print("\n3. Testing List Sessions (get_user_chat_sessions)...")
    try:
        sessions = await firebase_service.get_user_chat_sessions(user_id)
        found = any(s.get('sessionId') == session_id for s in sessions)
        if found:
            print(
                f"[OK] Created session found in user's list. Total sessions: {len(sessions)}")
        else:
            print(
                f"[FAIL] Created session NOT found in list. Total sessions: {len(sessions)}")
            print("   Listing first 3 sessions found:")
            for s in sessions[:3]:
                print(f"   - {s.get('sessionId')} (User: {s.get('userId')})")
    except Exception as e:
        print(f"[FAIL] Error listing sessions: {e}")

    print("\n4. Testing Message Generation (generate_response)...")
    try:
        reply = await langchain_service.generate_response(
            session_id=session_id,
            user_id=user_id,
            user_message="Hello, test message"
        )
        print(f"[OK] Message sent. Reply: {reply[:50]}...")
    except Exception as e:
        print(f"[FAIL] Message generation failed: {e}")

    # Clean up
    print("\n5. Cleaning up...")
    try:
        await firebase_service.delete_chat_session(session_id)
        print("[OK] Session deleted.")
    except Exception as e:
        print(f"[WARN] Cleanup failed: {e}")

if __name__ == "__main__":
    # Use a dummy ID or passed ID
    target_uid = "test_user_uid_123"
    if len(sys.argv) > 1:
        target_uid = sys.argv[1]

    asyncio.run(test_session_flow(target_uid))
