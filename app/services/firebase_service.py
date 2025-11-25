"""
Firebase service for Firestore and Authentication operations
"""
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

from app.config import settings
from app.models.user import User, UserProfile # Assuming these models are Pydantic or have a .model_dump() / .dict() method


# Helper function to convert the custom User model to a Firestore-safe dictionary
# This function assumes that the User object has a .model_dump() (Pydantic V2) or .dict() (Pydantic V1) method.
def user_to_firestore_dict(user_model: User) -> Dict[str, Any]:
    """Converts a User model instance to a dictionary, handling datetime conversion."""
    
    # Try Pydantic V2 method first, then V1 method
    try:
        user_dict = user_model.model_dump()
    except AttributeError:
        # Fallback for Pydantic V1 or similar models
        user_dict = user_model.dict()

    # Firestore handles datetime objects directly, but ensure they are included
    # We should also ensure the 'uid' is correctly named if it was defined as 'id' in the Pydantic model
    
    # Example conversion for Pydantic models with datetime fields:
    if 'created_at' in user_dict and isinstance(user_dict['created_at'], datetime):
        # Firestore SDK handles datetime objects, so this is usually fine
        pass 

    if 'updated_at' in user_dict and isinstance(user_dict['updated_at'], datetime):
        # Firestore SDK handles datetime objects, so this is usually fine
        pass
    
    return user_dict


class FirebaseService:
    """Service for Firebase operations"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one Firebase instance"""
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        if not FirebaseService._initialized:
            self._initialize_firebase()
            self.db = firestore.client()
            FirebaseService._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with credentials"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            print("Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            if settings.DEV_MODE and settings.FIREBASE_EMULATOR_HOST:
                # Use emulator for development
                os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIREBASE_EMULATOR_HOST
                firebase_admin.initialize_app()
                print(f"Firebase initialized with emulator: {settings.FIREBASE_EMULATOR_HOST}")
            else:
                # Use production credentials
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
                print("Firebase initialized with production credentials")
    
    # ============================================
    # USER OPERATIONS
    # ============================================
    
    async def create_user(self, email: str, password: str, display_name: str, 
                          role: str = "user", phone_number: Optional[str] = None) -> User:
        """
        Create a new user in Firebase Authentication and Firestore
        
        Args:
            email: User's email
            password: User's password
            display_name: User's display name
            role: User's role (default: "user")
            phone_number: Optional phone number
            
        Returns:
            User object
        """
        try:
            # Create user in Firebase Authentication
            firebase_user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                phone_number=phone_number
            )
            
            # Create user document in Firestore using the Pydantic model for structure
            # FIX: Added 'profile_picture' attribute which was causing the AttributeError
            user = User(
                uid=firebase_user.uid,
                email=email,
                display_name=display_name,
                role=role,
                phone_number=phone_number,
                email_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                profile_picture=firebase_user.photo_url if hasattr(firebase_user, 'photo_url') else None 
            )
            
            # Save to Firestore (FIXED: replaced user.to_dict() with helper function 
            # to prevent Attribute Error and handle Pydantic/dataclass serialization)
            firestore_data = user_to_firestore_dict(user)

            # In Firestore, we often use snake_case for fields, 
            # but Pydantic might use camelCase, so verify your model uses snake_case 
            # (or adjust the names here) to match your Firestore expectations.
            
            self.db.collection('users').document(firebase_user.uid).set(firestore_data)
            
            return user
            
        except firebase_auth.EmailAlreadyExistsError:
            raise ValueError("Email already exists")
        except Exception as e:
            # Log the specific error for better debugging
            print(f"DEBUG: Failed to create user or save to Firestore: {str(e)}")
            raise Exception(f"Error creating user: {str(e)}")
    
    async def get_user_by_uid(self, uid: str) -> Optional[User]:
        """
        Get user by UID from Firestore
        
        Args:
            uid: User's unique identifier
            
        Returns:
            User object or None if not found
        """
        try:
            doc = self.db.collection('users').document(uid).get()
            if doc.exists:
                # Assuming User.from_dict() exists and correctly handles the conversion
                return User.from_dict(doc.to_dict())
            return None
        except Exception as e:
            raise Exception(f"Error getting user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email from Firestore
        
        Args:
            email: User's email
            
        Returns:
            User object or None if not found
        """
        try:
            users_ref = self.db.collection('users')
            # NOTE: This query requires an index on the 'email' field in Firestore!
            query = users_ref.where('email', '==', email).limit(1).stream()
            
            for doc in query:
                return User.from_dict(doc.to_dict())
            
            return None
        except Exception as e:
            raise Exception(f"Error getting user by email: {str(e)}")
    
    async def update_user(self, uid: str, data: Dict[str, Any]) -> User:
        """
        Update user information in Firestore
        
        Args:
            uid: User's unique identifier
            data: Dictionary of fields to update
            
        Returns:
            Updated User object
        """
        try:
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow() # Note: changed key from 'updatedAt' to 'updated_at' for consistency
            
            # Update Firestore
            user_ref = self.db.collection('users').document(uid)
            user_ref.update(data)
            
            # Also update Firebase Auth if display name changed
            if 'display_name' in data: # Note: changed key from 'displayName' to 'display_name'
                firebase_auth.update_user(uid, display_name=data['display_name'])
            
            # Get and return updated user
            return await self.get_user_by_uid(uid)
            
        except Exception as e:
            raise Exception(f"Error updating user: {str(e)}")
    
    async def delete_user(self, uid: str) -> bool:
        """
        Delete user from Firebase Authentication and Firestore
        
        Args:
            uid: User's unique identifier
            
        Returns:
            True if successful
        """
        try:
            # Delete from Firebase Authentication
            firebase_auth.delete_user(uid)
            
            # Delete from Firestore
            self.db.collection('users').document(uid).delete()
            
            return True
        except Exception as e:
            raise Exception(f"Error deleting user: {str(e)}")
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token
        
        Args:
            id_token: Firebase ID token to verify
            
        Returns:
            Decoded token claims
        """
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            raise Exception(f"Invalid token: {str(e)}")
    
    # ============================================
    # USER PROFILE OPERATIONS
    # ============================================
    
    async def get_user_profile(self, uid: str) -> Optional[UserProfile]:
        """
        Get user profile from Firestore
        
        Args:
            uid: User's unique identifier
            
        Returns:
            UserProfile object or None if not found
        """
        try:
            doc = self.db.collection('user_profiles').document(uid).get()
            if doc.exists:
                # Assuming UserProfile.from_dict() exists and correctly handles the conversion
                return UserProfile.from_dict(doc.to_dict())
            return None
        except Exception as e:
            raise Exception(f"Error getting user profile: {str(e)}")
    
    async def update_user_profile(self, uid: str, profile_data: Dict[str, Any]) -> UserProfile:
        """
        Update or create user profile
        
        Args:
            uid: User's unique identifier
            profile_data: Profile data to update
            
        Returns:
            Updated UserProfile object
        """
        try:
            profile_ref = self.db.collection('user_profiles').document(uid)
            
            # Check if profile exists
            doc = profile_ref.get()
            if not doc.exists:
                # Create new profile
                # Assuming UserProfile model is initialized with uid and data, and has a dict/model_dump method
                profile = UserProfile(uid=uid, **profile_data)
                
                # FIX: Use the helper function here too, if UserProfile lacks .to_dict()
                try:
                    profile_dict = profile.model_dump()
                except AttributeError:
                    try:
                        profile_dict = profile.dict()
                    except AttributeError:
                        # Fallback if neither Pydantic method exists, assuming it's a simple object
                        profile_dict = profile.__dict__ 

                profile_ref.set(profile_dict)
            else:
                # Update existing profile
                profile_ref.update(profile_data)
            
            return await self.get_user_profile(uid)
            
        except Exception as e:
            raise Exception(f"Error updating user profile: {str(e)}")


# Global Firebase service instance
firebase_service = FirebaseService()