"""Test the working embedding models."""
import requests
import re

key = re.search(r"GOOGLE_API_KEY=(.+)", open(".env").read()).group(1).strip().strip('"').strip("'")

for model in ["gemini-embedding-001", "gemini-embedding-2"]:
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:embedContent?key={key}"
    payload = {
        "model": f"models/{model}",
        "content": {"parts": [{"text": "employee rights upon wrongful dismissal under Cameroonian labour law"}]},
        "taskType": "RETRIEVAL_DOCUMENT"
    }
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code == 200:
        emb = r.json().get("embedding", {}).get("values", [])
        print(f"[OK] models/{model}: dim={len(emb)}")
    else:
        print(f"[ERR] models/{model}: {r.status_code} - {r.json().get('error',{}).get('message','?')[:100]}")
