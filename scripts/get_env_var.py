import json
import os

try:
    with open("firebase-credentials.json", "r") as f:
        data = json.load(f)
        print("\nCOPY THE FOLLOWING LINE FOR 'FIREBASE_CREDENTIALS_JSON' IN RENDER:\n")
        print(json.dumps(data, separators=(',', ':')))
        print("\n")
except FileNotFoundError:
    print("Error: firebase-credentials.json not found in current directory.")
