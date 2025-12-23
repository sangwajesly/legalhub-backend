
from app.models.user import User
from app.services.firebase_service import firebase_service
from app.config import settings
import asyncio
import os
import sys

# Ensure app is in path
sys.path.append(os.getcwd())


async def test_lookup(email: str):
    print(f"--- Testing User Lookup for {email} ---")

    # 1. Direct Firebase Service Lookup
    print("\n1. Calling firebase_service.get_user_by_email...")
    try:
        user = await firebase_service.get_user_by_email(email)
        if user:
            print(f"✅ Found user by email: {user.uid}")
            print(f"Role: {user.role}")
        else:
            print("❌ Not found by email.")
    except Exception as e:
        print(f"❌ Error in get_user_by_email: {e}")
        import traceback
        traceback.print_exc()

    # 2. Simulate UID lookup (if we found one, or try a dummy)
    uid = user.uid if user else "dummy_uid"
    print(f"\n2. Calling firebase_service.get_user_by_uid({uid})...")
    try:
        user_by_id = await firebase_service.get_user_by_uid(uid)
        if user_by_id:
            print(f"✅ Found user by UID: {user_by_id.uid}")
            print(f"Data: {user_by_id.model_dump()}")
        else:
            print("❌ Not found by UID.")
    except Exception as e:
        print(f"❌ Error in get_user_by_uid: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_email = sys.argv[1]
    else:
        target_email = "sangwajesly82@gmail.com"

    asyncio.run(test_lookup(target_email))
