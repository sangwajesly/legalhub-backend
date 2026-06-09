"""
Full Firestore + Storage audit for LegalHub backend.
Covers: users, chat_sessions, cases, lawyers, bookings,
        organizations, articles, direct_messages, user_profiles
Also checks Firebase Storage accessibility.
"""
import firebase_admin
from firebase_admin import credentials, firestore, storage as fb_storage
from app.config import settings
import json
from datetime import datetime

TARGET_COLLECTIONS = [
    "users",
    "chat_sessions",
    "cases",
    "lawyers",
    "bookings",
    "organizations",
    "articles",
    "direct_messages",
    "user_profiles",
]


def serialize(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [serialize(i) for i in v]
    if isinstance(v, dict):
        return {k2: serialize(v2) for k2, v2 in v.items()}
    if not isinstance(v, (str, int, float, bool, type(None))):
        return str(v)
    return v


def audit():
    # ------------------------------------------------------------------
    # Firebase init
    # ------------------------------------------------------------------
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(
            cred, {"storageBucket": "legahub-70645.firebasestorage.app"}
        )

    db = firestore.client()

    # ------------------------------------------------------------------
    # 1. List ALL top-level collections
    # ------------------------------------------------------------------
    print("\n=== TOP-LEVEL COLLECTIONS ===")
    try:
        all_cols = [c.id for c in db.collections()]
        print(f"Found collections: {all_cols}")
    except Exception as e:
        all_cols = []
        print(f"Could not list collections: {e}")

    # ------------------------------------------------------------------
    # 2. Audit each target collection
    # ------------------------------------------------------------------
    print("\n=== COLLECTION AUDIT ===")
    results = {}
    for coll_name in TARGET_COLLECTIONS:
        try:
            docs = list(db.collection(coll_name).limit(3).stream())
            if not docs:
                results[coll_name] = {
                    "status": "EXISTS_EMPTY",
                    "doc_count": 0,
                    "fields": [],
                }
                print(f"COLLECTION: {coll_name} — EXISTS (EMPTY)")
            else:
                sample_doc = docs[0].to_dict()
                fields = sorted(sample_doc.keys())
                results[coll_name] = {
                    "status": "EXISTS_WITH_DATA",
                    "doc_count": len(docs),
                    "fields": fields,
                }
                print(
                    f"COLLECTION: {coll_name} — EXISTS, {len(docs)} doc(s) sampled, "
                    f"fields: {fields}"
                )
        except Exception as e:
            results[coll_name] = {"status": "ERROR", "error": str(e)}
            print(f"COLLECTION: {coll_name} — ERROR: {e}")

    # Check any additional discovered collections not in target list
    extra = [c for c in all_cols if c not in TARGET_COLLECTIONS]
    if extra:
        print(f"\nExtra collections found (not in target list): {extra}")
        for coll_name in extra:
            try:
                docs = list(db.collection(coll_name).limit(1).stream())
                fields = sorted(docs[0].to_dict().keys()) if docs else []
                results[coll_name] = {
                    "status": "EXISTS_WITH_DATA" if docs else "EXISTS_EMPTY",
                    "doc_count": len(docs),
                    "fields": fields,
                }
                print(
                    f"COLLECTION: {coll_name} — EXISTS, {len(docs)} doc(s) sampled, "
                    f"fields: {fields}"
                )
            except Exception as e:
                results[coll_name] = {"status": "ERROR", "error": str(e)}

    # ------------------------------------------------------------------
    # 3. Storage check
    # ------------------------------------------------------------------
    print("\n=== STORAGE AUDIT ===")
    storage_result = {}
    try:
        bucket = fb_storage.bucket()
        blobs = list(bucket.list_blobs(max_results=10))
        storage_result["status"] = "accessible"
        storage_result["bucket"] = bucket.name
        storage_result["sample_files"] = [b.name for b in blobs]
        print(f"STORAGE: accessible — bucket={bucket.name}, files={[b.name for b in blobs]}")
    except Exception as e:
        storage_result["status"] = "not accessible"
        storage_result["error"] = str(e)
        print(f"STORAGE: not accessible — {e}")

    # ------------------------------------------------------------------
    # 4. Print final structured report
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("FINAL AUDIT REPORT")
    print("=" * 60)
    print(f"Firebase Project: legahub-70645")
    print(f"All top-level collections: {all_cols}\n")

    for coll_name in TARGET_COLLECTIONS:
        r = results.get(coll_name, {})
        status = r.get("status", "MISSING")
        if status == "EXISTS_WITH_DATA":
            n = r["doc_count"]
            fields = r["fields"]
            print(f"COLLECTION: {coll_name} — EXISTS, {n} docs sampled, fields: {fields}")
        elif status == "EXISTS_EMPTY":
            print(f"COLLECTION: {coll_name} — EXISTS (EMPTY)")
        elif status == "ERROR":
            print(f"COLLECTION: {coll_name} — ERROR: {r.get('error')}")
        else:
            print(f"COLLECTION: {coll_name} — MISSING")

    if extra:
        print(f"\nADDITIONAL COLLECTIONS FOUND: {extra}")
        for coll_name in extra:
            r = results.get(coll_name, {})
            status = r.get("status", "MISSING")
            if status == "EXISTS_WITH_DATA":
                print(f"COLLECTION: {coll_name} — EXISTS, {r['doc_count']} docs sampled, fields: {r['fields']}")
            elif status == "EXISTS_EMPTY":
                print(f"COLLECTION: {coll_name} — EXISTS (EMPTY)")

    st = storage_result.get("status", "unknown")
    if st == "accessible":
        files = storage_result.get("sample_files", [])
        print(f"\nSTORAGE: accessible — bucket={storage_result.get('bucket')}, sample files: {files if files else '(none found in first 10)'}")
    else:
        print(f"\nSTORAGE: not accessible — {storage_result.get('error', '')}")

    print("=" * 60)


if __name__ == "__main__":
    audit()
