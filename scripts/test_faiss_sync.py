import sys
sys.path.insert(0, '.')
from app.utils.faiss_store import get_vector_store

vs = get_vector_store()
count = vs.count()
print(f"Chunks in store: {count}")

results = vs.search("theft punishment Cameroon penal code", top_k=2)
for r in results:
    sc = r.get("score", 0)
    src = r.get("source", "?")
    content = r.get("content", "")[:120]
    print(f"  score={sc:.3f}  source={src}")
    print(f"  preview: {content}...")

print("\nSyncing to Firebase Storage...")
ok = vs.sync_to_firebase()
print(f"Sync result: {ok}")
