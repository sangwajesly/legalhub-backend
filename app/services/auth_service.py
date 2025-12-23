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


def verify_id_token(id_token: str) -> dict:
    """Convenience wrapper to verify Firebase ID tokens for simple use in routes/tests."""
    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception as e:
        # Re-raise the exception to be caught by the dependency that calls this
        raise ValueError(f"Firebase ID token verification failed: {e}") from e


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
                email_verified=False,  # Explicitly set for new registrations
                is_new_user=True,  # Explicitly set for new registrations
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

    async def login_user(self, id_token: str) -> Dict[str, Any]:
        """
        Authenticate user via Firebase ID token and generate internal tokens.

        Args:
            id_token: Firebase ID token obtained from the client-side authentication.

        Returns:
            Dictionary containing user and internal tokens.

        Raises:
            ValueError: If the ID token is invalid or user not found.
        """
        try:
            # 1. Verify the Firebase ID token
            decoded_token = verify_id_token(id_token)
            if not decoded_token:
                raise ValueError("Invalid Firebase ID token.")

            uid = decoded_token.get("uid")
            email = decoded_token.get("email")

            if not uid or not email:
                raise ValueError("Firebase ID token missing UID or email.")

            # 2. Get user from our Firestore database
            user = await self.firebase.get_user_by_uid(uid)
            if not user:
                # If user exists in Firebase Auth but not in our Firestore, create them
                # This handles cases where a user logs in via Firebase Auth for the first time
                # but hasn't been synced to our Firestore 'users' collection yet.
                user = await self.firebase.create_user(
                    email=email,
                    # Password is not needed here as Firebase Auth has already verified it
                    password=None,  # Explicitly mark as not used for this path
                    display_name=decoded_token.get(
                        "name", email.split("@")[0]),
                    role="user",  # Default role
                    phone_number=decoded_token.get("phone_number"),
                    email_verified=decoded_token.get("email_verified", False),
                    photo_url=decoded_token.get("picture"),
                    is_new_user=False  # Not a new user from this path in create_user context
                )

            # 3. Create internal tokens (access and refresh)
            tokens = create_token_pair(
                user_id=user.uid, email=user.email, role=user.role
            )

            return {"user": user, "tokens": tokens}

        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")

    async def login_with_email_password(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with email and password via Firebase REST API.

        Args:
            email: User's email
            password: User's password

        Returns:
            Dictionary containing user and internal tokens (same as login_user)
        """
        try:
            import httpx
            from app.config import settings

            api_key = settings.GOOGLE_API_KEY
            if not api_key:
                raise ValueError("Google API Key not configured")

            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get(
                    "message", "Unknown error")
                raise ValueError(f"Authentication failed: {error_msg}")

            data = response.json()
            id_token = data.get("idToken")

            # Delegate to existing login_user logic which handles DB sync and internal tokens
            return await self.login_user(id_token)

        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Email/Password login failed: {str(e)}")

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
                # 3. Create new user in user_profiles (for social login)
                # We store Google/Social users in user_profiles collection as per requirement
                display_name = decoded_token.get("name", "")
                picture = decoded_token.get("picture", None)

                # Construct profile data including auth fields
                profile_data = {
                    "uid": uid,
                    "email": email,
                    "role": "user",
                    "displayName": display_name,
                    "profilePicture": picture,
                    "emailVerified": decoded_token.get("email_verified", False),
                    "bio": f"Joined via Google Login",
                    "createdAt": datetime.now(UTC),
                    "updatedAt": datetime.now(UTC)
                }

                # Use update_user_profile to create/set the document
                await self.firebase.update_user_profile(uid, profile_data)

                # Return a User object representing this new user
                user = User(
                    uid=uid,
                    email=email,
                    display_name=display_name,
                    role="user",
                    profile_picture=picture,
                    email_verified=decoded_token.get("email_verified", False),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )

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
                        # Update user profile in Firestore (user_profiles for social users)
                        # We use update_user_profile which targets 'user_profiles'
                        profile_update = {}
                        if "display_name" in update_data:
                            profile_update["displayName"] = update_data["display_name"]
                        if "profile_picture" in update_data:
                            profile_update["profilePicture"] = update_data["profile_picture"]

                        if profile_update:
                            await self.firebase.update_user_profile(uid, profile_update)

                            # Update local user object to return updated info
                            if "display_name" in update_data:
                                user.display_name = update_data["display_name"]
                            if "profile_picture" in update_data:
                                user.profile_picture = update_data["profile_picture"]

                    except Exception as e:
                        print(
                            f"DEBUG: Failed to auto-update user profile: {e}")
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
