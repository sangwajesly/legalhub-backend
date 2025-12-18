import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import random

# Import necessary models and services from your application
from app.models.lawyer import Lawyer, lawyer_model_to_firestore
from app.services.firebase_service import firebase_service
from app.models.user import User
from app.utils.security import hash_password # Assuming you have this for user creation

# --- Configuration for seeding ---
NUM_LAWYERS_TO_CREATE = 5

# --- Helper functions for dummy data generation ---
def generate_dummy_lawyer_data(uid: str, email: str, display_name: str) -> Lawyer:
    """Generates a dummy Lawyer object."""
    practice_areas = [
        "Criminal Law", "Civil Law", "Family Law", "Corporate Law",
        "Environmental Law", "Intellectual Property", "Real Estate Law"
    ]
    jurisdictions = ["Cameroon", "Douala", "Yaounde", "Bafoussam"]
    languages = ["English", "French"]

    return Lawyer(
        uid=uid,
        display_name=display_name,
        email=email,
        profile_picture=f"https://api.dicebear.com/7.x/initials/svg?seed={display_name}",
        bio=f"Experienced lawyer specializing in {random.choice(practice_areas)}.",
        location=random.choice(jurisdictions),
        license_number=f"LIC-{random.randint(10000, 99999)}",
        jurisdictions=random.sample(jurisdictions, k=random.randint(1, len(jurisdictions))),
        practice_areas=random.sample(practice_areas, k=random.randint(1, len(practice_areas))),
        hourly_rate=round(random.uniform(50.0, 300.0), 2),
        years_experience=random.randint(3, 30),
        languages=random.sample(languages, k=random.randint(1, len(languages))),
        verified=random.choice([True, False]),
        rating=round(random.uniform(3.0, 5.0), 1),
        num_reviews=random.randint(0, 200),
        created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365*5)),
        updated_at=datetime.now(timezone.utc),
    )

async def seed_lawyers():
    """
    Seeds the Firestore database with dummy lawyer and corresponding user data.
    """
    print(f"--- Seeding {NUM_LAWYERS_TO_CREATE} dummy lawyers ---")
    
    for i in range(NUM_LAWYERS_TO_CREATE):
        # 1. Create dummy user data (needed for Firebase Auth and 'users' collection)
        email = f"lawyer{i+1}@example.com"
        password = "Password123" # Dummy password for auth creation
        display_name = f"Lawyer Name {i+1}"
        
        # Ensure the user exists in Firebase Auth and Firestore's 'users' collection
        # We use firebase_service.create_user to handle both
        try:
            print(f"Creating user for {email}...")
            user_model: User = await firebase_service.create_user(
                email=email,
                password=password,
                display_name=display_name,
                role="lawyer", # Assign 'lawyer' role to the user
                is_new_user=True,
                email_verified=True,
            )
            uid = user_model.uid
            print(f"User {email} created with UID: {uid}")

            # 2. Generate dummy lawyer profile data
            lawyer_data = generate_dummy_lawyer_data(uid, email, display_name)
            
            # 3. Save lawyer profile to Firestore 'lawyers' collection
            # Ensure the uid of the Lawyer model matches the firebase_user.uid
            # The lawyer_model_to_firestore helper will handle field mapping
            firestore_data = lawyer_model_to_firestore(lawyer_data)

            await asyncio.to_thread(firebase_service.db.collection("lawyers").document(uid).set, firestore_data)
            print(f"Lawyer profile for {display_name} saved to Firestore (UID: {uid}).")

        except ValueError as e:
            if "Email already exists" in str(e):
                print(f"User with email {email} already exists. Attempting to update lawyer profile.")
                user_model = await firebase_service.get_user_by_email(email)
                if user_model:
                    uid = user_model.uid
                    lawyer_data = generate_dummy_lawyer_data(uid, email, display_name)
                    # Use lawyer_model_to_firestore for consistency
                    firestore_data = lawyer_model_to_firestore(lawyer_data) 
                    try:
                        await firebase_service.db.collection("lawyers").document(uid).set(firestore_data)
                        print(f"Lawyer profile for {display_name} updated in Firestore (UID: {uid}).")
                    except Exception as update_e:
                        print(f"Error updating lawyer profile for {email}: {update_e}")
                else:
                    print(f"User {email} exists in Firebase Auth but not in Firestore 'users' collection. Skipping lawyer profile update.")
            else:
                print(f"Error creating user {email}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {email}: {e}")
            
    print("--- Lawyer seeding complete ---")

if __name__ == "__main__":
    # Ensure Firebase is initialized (FirebaseService is a singleton)
    _ = firebase_service 
    asyncio.run(seed_lawyers())
