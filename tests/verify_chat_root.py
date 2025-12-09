
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_chat_root():
    url = f"{BASE_URL}/api/chat"
    try:
        # Note: Depending on auth setup, this might fail with 401 if we don't assume a mock user or similar.
        # However, looking at the code `user: Optional[dict] = Depends(get_current_user)`, it seems optional? 
        # Wait, usually `get_current_user` raises 401 if not found. 
        # Let's check `app/dependencies.py` to see if get_current_user enforces auth.
        # If it does, we might get a 401 instead of 404, which is still progress (route found).
        # But if the user is Optional in the router function, maybe it depends on the dependency implementation.
        
        # Let's try sending a request.
        response = requests.post(url, json={})
        
        print(f"POST {url} -> Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 404:
            print("FAILURE: Still getting 404")
            sys.exit(1)
        elif response.status_code in [200, 201]:
            data = response.json()
            if "sessionId" in data:
                print("SUCCESS: Received sessionId")
                sys.exit(0)
            else:
                print("FAILURE: JSON missing sessionId")
                sys.exit(1)
        elif response.status_code == 401:
            print("SUCCESS (Partial): 401 Unauthorized means the route exists!")
            sys.exit(0)
        else:
            print(f"FAILURE: Unexpected status code {response.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_chat_root()
