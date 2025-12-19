import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
import json
from datetime import datetime


async def inspect():
    print("Starting inspection...")
    if not firebase_admin._apps:
        print(
            f"Initializing Firebase with: {settings.FIREBASE_CREDENTIALS_PATH}")
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized.")

    print("Getting Firestore client...")
    db = firestore.client()
    print("Firestore client obtained.")

    collections = ['users', 'articles', 'bookings',
                   'cases', 'lawyers', 'organizations', 'settings']

    report = {}

    for coll_name in collections:
        print(f"Inspecting collection: {coll_name}")
        try:
            # Synchronous call in Firebase Admin SDK
            docs_iter = db.collection(coll_name).limit(3).get()
            print(f"Fetched documents for {coll_name}")

            doc_samples = []
            for doc in docs_iter:
                data = doc.to_dict()
                # Convert datetime and other non-serializable objects to string
                serializable_data = {}
                for k, v in data.items():
                    if isinstance(v, datetime):
                        serializable_data[k] = v.isoformat()
                    elif hasattr(v, '__str__') and not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                        serializable_data[k] = str(v)
                    else:
                        serializable_data[k] = v
                doc_samples.append({
                    "id": doc.id,
                    "data": serializable_data
                })

            report[coll_name] = doc_samples
            print(f"Processed {len(doc_samples)} documents for {coll_name}")
        except Exception as e:
            print(f"Error inspecting collection {coll_name}: {e}")
            report[coll_name] = {"error": str(e)}

    print("Writing report to JSON...")
    with open("firestore_inspection_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("Inspection complete. Report saved to firestore_inspection_report.json")

if __name__ == "__main__":
    asyncio.run(inspect())
