from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from app.dependencies import get_current_user
from app.services import firebase_service, langchain_service
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])


class CreateSessionResponse(BaseModel):
	sessionId: str


class MessageRequest(BaseModel):
	sessionId: Optional[str]
	message: str


class MessageResponse(BaseModel):
	reply: str
	sessionId: str


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(user=Depends(get_current_user)):
	session_id = str(uuid.uuid4())
	await langchain_service.create_session(user.get("uid"), session_id)
	return {"sessionId": session_id}


@router.delete("/session/{id}")
async def delete_session(id: str, user=Depends(get_current_user)):
	try:
		firebase_service.delete_chat_session(id)
	except Exception:
		raise HTTPException(status_code=404, detail="Session not found or delete failed")
	return {"ok": True}


@router.post("/message", response_model=MessageResponse)
async def send_message(payload: MessageRequest, user=Depends(get_current_user)):
	# create session if missing
	session_id = payload.sessionId or str(uuid.uuid4())
	if not payload.sessionId:
		await langchain_service.create_session(user.get("uid"), session_id)

	# call LangChain service
	reply_text = await langchain_service.generate_response(
		session_id=session_id,
		user_id=user.get("uid"),
		user_message=payload.message
	)

	return {"reply": reply_text, "sessionId": session_id}


@router.get("/history")
async def get_history(sessionId: str, user=Depends(get_current_user)):
	try:
		msgs = firebase_service.get_chat_history(sessionId)
	except Exception:
		msgs = []
	return {"messages": msgs}


@router.post("/feedback")
async def feedback(sessionId: str, messageId: str, rating: int = 0, user=Depends(get_current_user)):
	# store feedback in a collection
	try:
		db = firebase_service.get_firestore()
		db.collection("chat_feedback").add({"sessionId": sessionId, "messageId": messageId, "rating": rating})
	except Exception:
		pass
	return {"ok": True}

