from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services import auth_service, firebase_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenRequest(BaseModel):
	idToken: str
	displayName: str | None = None


class AuthResponse(BaseModel):
	uid: str
	email: str | None = None
	displayName: str | None = None


@router.post("/register", response_model=AuthResponse)
async def register(payload: TokenRequest):
	decoded = auth_service.verify_id_token(payload.idToken)
	if not decoded:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token")
	uid = decoded.get("uid")
	user_data = {"email": decoded.get("email"), "displayName": payload.displayName or decoded.get("name")}
	firebase_service.create_user(uid, user_data)
	return {"uid": uid, **user_data}


@router.post("/login", response_model=AuthResponse)
async def login(payload: TokenRequest):
	decoded = auth_service.verify_id_token(payload.idToken)
	if not decoded:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token")
	uid = decoded.get("uid")
	# Ensure user exists in Firestore
	firebase_service.create_user(uid, {"email": decoded.get("email"), "displayName": decoded.get("name")})
	return {"uid": uid, "email": decoded.get("email"), "displayName": decoded.get("name")}
