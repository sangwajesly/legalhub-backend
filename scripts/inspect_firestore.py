import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
import json
from datetime import datetime


async def inspect():
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    collections = ['users', 'articles', 'bookings',
                   'cases', 'lawyers', 'organizations']

    report = {}

    for coll_name in collections:
        print(f"Inspecting collection: {coll_name}")
        docs = db.collection(coll_name).limit(3).get()

        doc_samples = []
        for doc in docs:
            data = doc.to_dict()
            # Convert datetime to string for JSON serialization
            serializable_data = {}
            for k, v in data.items():
                if isinstance(v, datetime):
                    serializable_data[k] = v.isoformat()
                else:
                    serializable_data[k] = v
            doc_samples.append({
                "id": doc.id,
                "data": serializable_data
            })

        report[coll_name] = doc_samples

    with open("firestore_inspection_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("Inspection complete. Report saved to firestore_inspection_report.json")

if __name__ == "__main__":
    asyncio.run(inspect())
