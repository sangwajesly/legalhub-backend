import asyncio
import httpx
from app.services.auth_service import auth_service
from app.utils.security import create_token_pair
from app.config import settings


async def test_chat_flow():
    email = "sangwajesly82@gmail.com"
    print(f"Testing chat flow for {email}...")

    # 1. Get User
    # We use our fixed get_user_by_uid which might fallback to Auth
    # But here we need to find the UID first.
    # Let's try to find by email first (which queries Firestore)
    # If not found in Firestore, we can't easily get UID without Firebase Admin SDK
    # But wait, check_user.py failed because of module import, but I fixed the get_user_by_uid.

    # We will try to get the user from Firestore directly via the service
    user = await auth_service.firebase.get_user_by_email(email)

    if not user:
        print("User not found in Firestore. Attempting to fetch by UID is hard without knowing UID.")
        print("Please ensure the user exists.")
        return

    print(f"User found: {user.uid}")

    # 2. Generate Token (Internal JWT)
    tokens = create_token_pair(user.uid, user.email, user.role)
    access_token = tokens["access_token"]
    print(f"Generated Access Token: {access_token[:20]}...")

    # 3. Test Create Session Endpoint
    url = f"http://127.0.0.1:8000/api/v1/chat/sessions"
    headers = {"Authorization": f"Bearer {access_token}"}

    print(f"POST {url}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, headers=headers)
            print(f"Response Status: {resp.status_code}")
            print(f"Response Body: {resp.text}")

            if resp.status_code == 200:
                print("✅ Success! Backend accepts the token and creates session.")
            elif resp.status_code == 401:
                print("❌ 401 Unauthorized. Backend rejected the token.")
            else:
                print("❌ Other Error.")

        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_flow())
