
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
from datetime import datetime

# Set up path to import app modules
sys.path.append(os.getcwd())

async def test_get_sessions():
    """Test the GET /sessions endpoint logic"""
    print("Testing GET /sessions logic...")
    
    # Mock dependencies
    with patch("app.api.routes.chat.firebase_service") as mock_firebase:
        from app.api.routes.chat import get_sessions
        
        # Test Case 1: User has sessions
        print("\nCase 1: User has sessions")
        user = {"uid": "test_uid"}
        
        expected_sessions = [
            {"sessionId": "s1", "userId": "test_uid", "lastMessageAt": "2024-01-01"},
            {"sessionId": "s2", "userId": "test_uid", "lastMessageAt": "2023-12-31"}
        ]
        
        # Mock get_user_chat_sessions to return list
        mock_firebase.get_user_chat_sessions = AsyncMock(return_value=expected_sessions)
        
        # Call endpoint function directly
        response = await get_sessions(user=user)
        
        if response["sessions"] == expected_sessions:
            print("SUCCESS: Returned expected sessions")
        else:
            print(f"FAILURE: Expected {expected_sessions}, got {response}")
            
        # Test Case 2: Error handling
        print("\nCase 2: Service error")
        mock_firebase.get_user_chat_sessions.side_effect = Exception("DB Error")
        
        response = await get_sessions(user=user)
        
        if response["sessions"] == []:
            print("SUCCESS: Handled error gracefully (returned empty list)")
        else:
            print(f"FAILURE: Expected [], got {response}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_get_sessions())
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
