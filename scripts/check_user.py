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

        # Check user_profiles
        print("\nChecking 'user_profiles' collection...")
        profiles_ref = db.collection("user_profiles")
        # Try to find by email if possible, or assuming we don't have UID, scan?
        # Ideally we search by email.
        query_prof = profiles_ref.where("email", "==", email).stream()

        found_prof = False
        for doc in query_prof:
            found_prof = True
            print(f"✅ User found in 'user_profiles'!")
            print(f"ID: {doc.id}")
            data = doc.to_dict()
            print(f"Data: {data}")

            # Helper to check validation
            from app.models.user import User
            try:
                # Mock missing fields if needed to simulate firebase_service logic
                # data["uid"] = doc.id
                # user = User.model_validate(data)
                print("Validation check would presumably run here.")
            except Exception as e:
                print(f"Validation Error would be: {e}")

        if not found_prof:
            print("❌ User NOT found in 'user_profiles' collection either.")
    else:
        print("User found in 'users', so auth should work if token is valid.")

if __name__ == "__main__":
    import sys
    # Default to the email from the screenshot if not provided
    target_email = "sangwajesly82@gmail.com"
    if len(sys.argv) > 1:
        target_email = sys.argv[1]

    asyncio.run(check_user(target_email))
