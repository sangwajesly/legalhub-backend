from app.config import settings
import sys

default_key = "AIzaSyC5mJNpSkdmp7jZBp2NwWjJjzzZILIkjjk"

print(f"Checking Google API Key configuration...")
print(f"----------------------------------------")

current_key = settings.GOOGLE_API_KEY

if current_key == default_key:
    print("❌ ERROR: You are using the default placeholder API Key.")
    print(f"   Value: {current_key}")
    print("   Please update 'GOOGLE_API_KEY' in your .env file with a valid key from Google AI Studio.")
    sys.exit(1)
else:
    print("✅ Key is different from default placeholder.")
    print(f"   Key value: {current_key[:5]}...{current_key[-5:]}")
    print("   If you still get 400 errors, please double-check that this key is valid and active.")
