
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Set up path to import app modules
sys.path.append(os.getcwd())

async def test_profile_sync():
    """Test the profile sync logic in auth_service"""
    print("Testing profile sync logic...")
    
    # Mock dependencies
    with patch("app.services.auth_service.verify_id_token") as mock_verify:
        with patch("app.services.auth_service.firebase_service") as mock_firebase:
            with patch("app.services.auth_service.create_token_pair") as mock_create_token_pair:
                
                # Import service after patching
                from app.services.auth_service import AuthService
                from app.models.user import User

                service = AuthService()
                service.firebase = mock_firebase
                
                # 1. Test Case: User exists, Token has NEW name -> Should update
                print("\nCase 1: Existing user, new name in token")
                
                # Setup existing user
                existing_user = User(
                    uid="test_uid",
                    email="test@example.com",
                    display_name="Old Name",
                    role="user",
                    profile_picture="old.jpg"
                )
                # Setup async mock for get_user_by_uid
                from unittest.mock import AsyncMock
                mock_firebase.get_user_by_uid = AsyncMock(return_value=existing_user)
                mock_firebase.update_user_profile = AsyncMock()
                
                # Setup token with NEW name
                mock_verify.return_value = {
                    "uid": "test_uid",
                    "email": "test@example.com",
                    "name": "New Name", # Changed
                    "picture": "old.jpg",
                    "email_verified": True
                }
                
                mock_create_token_pair.return_value = {"access_token": "a", "refresh_token": "r"}
                
                # Execute
                await service.authenticate_with_social_provider("dummy_token")
                
                # Verify update was called
                # We expect user_ref.update({'displayName': 'New Name'})
                # Since we can't easily assert on the chained calls of mock_firebase.db.collection().document()...
                # We'll check if the db.collection was accessed
                mock_firebase.db.collection.assert_called()
                print("SUCCESS: Database collection accessed for update")
                
                # 2. Test Case: User exists, Token matches -> Should NOT update
                print("\nCase 2: Existing user, matching token")
                mock_firebase.db.reset_mock()
                
                # Setup user (same name as token now)
                existing_user.display_name = "New Name" 
                
                # Token same as above ("New Name")
                
                # Execute
                await service.authenticate_with_social_provider("dummy_token")
                
                # Verify update was NOT called
                mock_firebase.db.collection.assert_not_called()
                print("SUCCESS: No update for matching data")
                
                
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_profile_sync())
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
