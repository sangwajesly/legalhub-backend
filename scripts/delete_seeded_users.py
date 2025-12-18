import asyncio
from firebase_admin import auth as firebase_auth
from app.services.firebase_service import firebase_service # To ensure Firebase is initialized

async def delete_all_seeded_users():
    """
    Deletes all users created by the seeding script (lawyer1@example.com, etc.)
    from Firebase Authentication and their corresponding Firestore documents.
    """
    print("--- Deleting seeded users from Firebase Authentication and Firestore ---")
    
    users_to_delete_auth_uids = []
    users_to_delete_firestore_uids = []

    for i in range(1, 6): # Assuming 5 lawyers were created
        email = f"lawyer{i}@example.com"
        try:
            user = await asyncio.to_thread(firebase_auth.get_user_by_email, email)
            users_to_delete_auth_uids.append(user.uid)
            users_to_delete_firestore_uids.append(user.uid)
            print(f"Found user {email} with UID: {user.uid} for deletion.")
        except firebase_auth.UserNotFoundError:
            print(f"User {email} not found in Firebase Auth. Checking Firestore directly...")
            # If not in Auth, still check Firestore in case of partial creation
            # We need to query by email, as we don't have UID without Auth
            try:
                # Use firebase_service to get user from Firestore by email
                user_from_firestore = await firebase_service.get_user_by_email(email)
                if user_from_firestore:
                    users_to_delete_firestore_uids.append(user_from_firestore.uid)
                    print(f"Found user {email} in Firestore with UID: {user_from_firestore.uid} for deletion.")
            except Exception as e:
                print(f"Error checking Firestore for user {email}: {e}")
        except Exception as e:
            print(f"Error checking user {email} in Firebase Auth: {e}")

    # Delete from Firebase Authentication
    if users_to_delete_auth_uids:
        try:
            await asyncio.to_thread(firebase_auth.delete_users, users_to_delete_auth_uids)
            print(f"Successfully deleted {len(users_to_delete_auth_uids)} users from Firebase Auth.")
        except Exception as e:
            print(f"Error deleting users from Firebase Auth: {e}")
    else:
        print("No seeded users found in Firebase Auth for deletion.")

    # Delete from Firestore 'users' and 'lawyers' collections
    if users_to_delete_firestore_uids:
        print("Attempting to delete corresponding Firestore documents...")
        for uid in users_to_delete_firestore_uids:
            try:
                await asyncio.to_thread(firebase_service.db.collection("users").document(uid).delete)
                print(f"Deleted user document {uid} from 'users' collection.")
            except Exception as e:
                print(f"Error deleting user document {uid} from 'users' collection: {e}")
            
            try:
                await asyncio.to_thread(firebase_service.db.collection("lawyers").document(uid).delete)
                print(f"Deleted lawyer document {uid} from 'lawyers' collection.")
            except Exception as e:
                print(f"Error deleting lawyer document {uid} from 'lawyers' collection: {e}")
    else:
        print("No seeded user documents found in Firestore for deletion.")
            
    print("--- Deletion complete ---")

if __name__ == "__main__":
    _ = firebase_service # Ensure Firebase is initialized
    asyncio.run(delete_all_seeded_users())
