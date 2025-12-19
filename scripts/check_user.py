import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings


async def check_user(email: str):
    print(f"Checking for user with email: {email}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Query users collection by email (this relies on the document containing the email field)
    # The user model stores 'email' field.

    # Note: Scanning all users if no index on email, but for debug it's fine or we use where
    users_ref = db.collection("users")
    query = users_ref.where("email", "==", email).stream()

    found = False
    for doc in query:
        found = True
        print(f"✅ User found!")
        print(f"ID: {doc.id}")
        print(f"Data: {doc.to_dict()}")

    if not found:
        print("❌ User NOT found in Firestore 'users' collection.")
        print("This explains the 401 error if the backend requires the user to exist in Firestore.")

if __name__ == "__main__":
    import sys
    # Default to the email from the screenshot if not provided
    target_email = "sangwajesly82@gmail.com"
    if len(sys.argv) > 1:
        target_email = sys.argv[1]

    asyncio.run(check_user(target_email))
