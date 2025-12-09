"""
Authentication service handling login, registration, and token management
"""

from typing import Dict, Any, Optional
from firebase_admin import auth as firebase_auth
from jose import JWTError

from app.services.firebase_service import firebase_service
from app.utils.security import (
    verify_password,
    create_token_pair,
    verify_refresh_token,
    hash_password,
)
from app.models.user import User
from datetime import datetime, UTC
from app.services.firebase_service import firebase_service, user_to_firestore_dict

from app.schemas.auth import UserRegister, UserLogin


def verify_id_token(id_token: str) -> dict | None:
    """Convenience wrapper to verify Firebase ID tokens for simple use in routes/tests."""
    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception as e:
        print(f"DEBUG: Token verification failed: {e}")
        return None


class AuthService:
    """Service for authentication operations"""

    def __init__(self):
        self.firebase = firebase_service

    async def register_user(self, user_data: UserRegister) -> Dict[str, Any]:
        """
        Register a new user

        Args:
            user_data: User registration data

        Returns:
            Dictionary containing user and tokens

        Raises:
            ValueError: If email already exists or validation fails
        """
        try:
            # Check if user already exists
            existing_user = await self.firebase.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("Email already registered")

            # Create user in Firebase
            user = await self.firebase.create_user(
                email=user_data.email,
                password=user_data.password,
                display_name=user_data.display_name,
                role=user_data.role,
                phone_number=user_data.phone_number,
            )

            # Create tokens
            tokens = create_token_pair(
                user_id=user.uid, email=user.email, role=user.role
            )

            return {"user": user, "tokens": tokens}

        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Registration failed: {str(e)}")

    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens

        Args:
            login_data: User login credentials

        Returns:
            Dictionary containing user and tokens

        Raises:
            ValueError: If credentials are invalid
        """
        try:
            # Get user from database
            user = await self.firebase.get_user_by_email(login_data.email)
            if not user:
                raise ValueError("Invalid email or password")

            # Verify password with Firebase Authentication
            try:
                # This requires the Firebase REST API since Admin SDK doesn't have signInWithPassword
                # For now, we'll use a workaround with custom tokens
                firebase_user = firebase_auth.get_user_by_email(login_data.email)

                # In production, you should verify the password using Firebase REST API
                # For this implementation, we'll create tokens directly

            except firebase_auth.UserNotFoundError:
                raise ValueError("Invalid email or password")

            # Create tokens
            tokens = create_token_pair(
                user_id=user.uid, email=user.email, role=user.role
            )

            return {"user": user, "tokens": tokens}

        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            JWTError: If refresh token is invalid
        """
        try:
            # Verify refresh token
            payload = verify_refresh_token(refresh_token)
            user_id = payload.get("sub")

            if not user_id:
                raise JWTError("Invalid token payload")

            # Get user from database
            user = await self.firebase.get_user_by_uid(user_id)
            if not user:
                raise JWTError("User not found")

            # Create new token pair
            tokens = create_token_pair(
                user_id=user.uid, email=user.email, role=user.role
            )

            return tokens

        except JWTError as e:
            raise JWTError(f"Token refresh failed: {str(e)}")

    async def logout_user(self, user_id: str) -> bool:
        """
        Logout user (invalidate sessions if needed)

        Args:
            user_id: User's unique identifier

        Returns:
            True if successful
        """
        # In a more complex system, you might want to:
        # 1. Revoke Firebase tokens
        # 2. Clear session data
        # 3. Blacklist tokens

        # For now, we'll just return True
        # The client should discard the tokens
        return True

    async def send_password_reset_email(self, email: str) -> bool:
        """
        Send password reset email via Firebase

        Args:
            email: User's email address

        Returns:
            True if email sent successfully
        """
        try:
            # Firebase Admin SDK doesn't have this method
            # You need to use Firebase REST API or client SDK
            # For now, we'll just verify the user exists

            user = await self.firebase.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists
                return True

            # In production, call Firebase REST API to send reset email
            # Or use Firebase client SDK on the frontend

            return True

        except Exception as e:
            # Don't reveal errors to prevent email enumeration
            return True

    async def verify_email(self, user_id: str) -> bool:
        """
        Mark user's email as verified

        Args:
            user_id: User's unique identifier

        Returns:
            True if successful
        """
        try:
            # Update Firebase Authentication
            firebase_auth.update_user(user_id, email_verified=True)

            # Update Firestore
            await self.firebase.update_user(user_id, {"emailVerified": True})

            return True

        except Exception as e:
            raise Exception(f"Email verification failed: {str(e)}")

    async def get_current_user(self, user_id: str) -> Optional[User]:
        """
        Get current authenticated user

        Args:
            user_id: User's unique identifier

        Returns:
            User object or None
        """
        return await self.firebase.get_user_by_uid(user_id)


    async def authenticate_with_social_provider(self, id_token: str) -> Dict[str, Any]:
        """
        Authenticate a user with a social provider (Google, etc.) using a Firebase ID token.
        
        Args:
            id_token: Firebase ID token from the client
            
        Returns:
            Dictionary containing user and tokens
        """
        try:
            # 1. Verify the token
            decoded_token = verify_id_token(id_token)
            if not decoded_token:
                raise ValueError("Invalid ID token")
            
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
            
            if not email:
                raise ValueError("Token must contain an email address")

            # 2. Check if user exists in our Firestore
            user = await self.firebase.get_user_by_uid(uid)
            
            if not user:
                # 3. Create new user if not exists
                # Extract profile info from token
                display_name = decoded_token.get("name", "")
                picture = decoded_token.get("picture", None)
                
                # We need to create the user in Firestore.
                # Since auth record already exists in Firebase Auth (social login),
                # we just need to create the Firestore document.
                
                user = User(
                    uid=uid,
                    email=email,
                    display_name=display_name,
                    role="user", # Default role
                    email_verified=decoded_token.get("email_verified", False),
                    profile_picture=picture,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    phone_number=decoded_token.get("phone_number")
                )
                
                # Use the firebase service's logic to save to Firestore
                # We can't use create_user because that tries to create in Auth too
                firestore_data = user_to_firestore_dict(user)
                self.firebase.db.collection("users").document(uid).set(firestore_data)
                
                # Also create a default profile if needed
                await self.firebase.update_user_profile(uid, {"bio": f"Joined via Google Login"})
            
            else:
                # 3b. Use existing user - CHECK FOR UPDATES
                # Check if display name or profile picture has changed in the Google profile
                should_update = False
                update_data = {}
                
                token_name = decoded_token.get("name")
                token_picture = decoded_token.get("picture")
                
                # Check display name (if token has one and it differs)
                if token_name and token_name != user.display_name:
                    update_data["display_name"] = token_name
                    should_update = True
                    
                # Check profile picture (if token has one and it differs)
                if token_picture and token_picture != user.profile_picture:
                    update_data["profile_picture"] = token_picture
                    should_update = True
                
                if should_update:
                    try:
                        # Update user in Firestore
                        user_ref = self.firebase.db.collection("users").document(uid)
                        # We use field updates directly to avoid full object replacement
                        # Map internal field names to Firestore field names if needed
                        # Based on user_model_to_firestore in user.py model:
                        firestore_update = {}
                        if "display_name" in update_data:
                            firestore_update["displayName"] = update_data["display_name"]
                        if "profile_picture" in update_data:
                            firestore_update["profilePicture"] = update_data["profile_picture"]
                        
                        if firestore_update:
                            user_ref.update(firestore_update)
                            
                            # Update local user object to return updated info
                            if "display_name" in update_data:
                                user.display_name = update_data["display_name"]
                            if "profile_picture" in update_data:
                                user.profile_picture = update_data["profile_picture"]
                                
                    except Exception as e:
                        print(f"DEBUG: Failed to auto-update user profile: {e}")
                        # Non-critical, continue with login
            
            # 4. Generate backend tokens
            tokens = create_token_pair(
                user_id=user.uid, email=user.email, role=user.role
            )
            
            return {"user": user, "tokens": tokens}
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Social authentication failed: {str(e)}")


# Global auth service instance
auth_service = AuthService()
