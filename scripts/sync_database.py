import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
from app.models.user import User, user_model_to_firestore
from app.models.lawyer import Lawyer, lawyer_model_to_firestore
from app.models.settings import SystemSettings, settings_model_to_firestore
from datetime import datetime, UTC


async def sync():
    print("Starting Database Synchronization...")

    if not firebase_admin._apps:
        print(
            f"Initializing Firebase with: {settings.FIREBASE_CREDENTIALS_PATH}")
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized.")

    db = firestore.client()

    # 1. Seed System Settings
    print("\n--- 1. Seeding System Settings ---")
    settings_ref = db.collection("settings").document("config")
    doc = settings_ref.get()

    if not doc.exists:
        print("Creating default system settings...")
        default_settings = SystemSettings()
        settings_ref.set(settings_model_to_firestore(default_settings))
        print("Default settings seeded.")
    else:
        print("System settings already exist. Patching missing fields...")
        existing_data = doc.to_dict()
        default_settings = SystemSettings()
        updated_data = {
            **default_settings.model_dump(by_alias=True), **existing_data}
        updated_data["updatedAt"] = datetime.now(UTC)
        settings_ref.update(updated_data)
        print("System settings patched.")

    # 2. Patch Users
    print("\n--- 2. Patching Users ---")
    users_ref = db.collection("users")
    user_docs = users_ref.stream()

    users_patched = 0
    for doc in user_docs:
        data = doc.to_dict()
        uid = doc.id

        # Ensure 'uid' is in data for validation if it's missing
        patch_data = {}

        # Check for essential fields and add defaults if missing
        changed = False

        # Basic fields that should always exist according to User model
        defaults = {
            "isActive": True,
            "isDeleted": False,
            "emailVerified": False,
        }

        for key, val in defaults.items():
            if key not in data:
                data[key] = val
                patch_data[key] = val
                changed = True

        if "createdAt" not in data:
            now = datetime.now(UTC)
            data["createdAt"] = now
            patch_data["createdAt"] = now
            changed = True

        if "updatedAt" not in data:
            now = datetime.now(UTC)
            data["updatedAt"] = now
            patch_data["updatedAt"] = now
            changed = True

        if changed:
            print(f"Patching user {uid} ({data.get('email', 'N/A')})...")
            users_ref.document(uid).update(patch_data)
            users_patched += 1

    print(f"Users checked. Patched: {users_patched}")

    # 3. Patch Lawyers
    print("\n--- 3. Patching Lawyers ---")
    lawyers_ref = db.collection("lawyers")
    lawyer_docs = lawyers_ref.stream()

    lawyers_patched = 0
    for doc in lawyer_docs:
        data = doc.to_dict()
        uid = doc.id

        patch_data = {}
        changed = False

        defaults = {
            "verified": False,
            "jurisdictions": [],
            "practiceAreas": [],
            "languages": [],
        }

        for key, val in defaults.items():
            if key not in data:
                data[key] = val
                patch_data[key] = val
                changed = True

        if changed:
            print(
                f"Patching lawyer {uid} ({data.get('displayName', 'N/A')})...")
            lawyers_ref.document(uid).update(patch_data)
            lawyers_patched += 1

    print(f"Lawyers checked. Patched: {lawyers_patched}")

    print("\nDatabase Synchronization Complete!")

if __name__ == "__main__":
    asyncio.run(sync())
