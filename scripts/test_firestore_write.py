import asyncio
from datetime import datetime, UTC
from app.services.firebase_service import firebase_service # To ensure Firebase is initialized

async def test_firestore_write():
    print("--- Testing direct Firestore write to 'users' collection ---")
    
    test_uid = "test_user_firestore_write_123"
    test_email = "test.user@example.com"
    test_display_name = "Test User"
    
    test_data = {
        "email": test_email,
        "displayName": test_display_name,
        "role": "user",
        "emailVerified": True,
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
    }
    
    try:
        print(f"Attempting to write document with UID '{test_uid}' to 'users' collection...")
        await firebase_service.db.collection("users").document(test_uid).set(test_data)
        print(f"Successfully wrote document with UID '{test_uid}'.")
        
        # Verify immediately
        doc = await firebase_service.db.collection("users").document(test_uid).get()
        if doc.exists:
            print(f"Verification successful: Document for '{test_uid}' found in Firestore.")
            print(f"Retrieved data: {doc.to_dict()}")
        else:
            print(f"Verification failed: Document for '{test_uid}' NOT found after write.")
            
    except Exception as e:
        print(f"Error during direct Firestore write test: {e}")
            
    print("--- Direct Firestore write test complete ---")

if __name__ == "__main__":
    _ = firebase_service # Ensure Firebase is initialized
    asyncio.run(test_firestore_write())
