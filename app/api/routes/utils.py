from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services import gemini_service
from app.dependencies import get_current_user
import logging

router = APIRouter(prefix="/api/v1/utils", tags=["utils"])
logger = logging.getLogger(__name__)

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Transcribe uploaded audio file to text using Gemini.
    Supported formats: webm, mp4, mp3, wav, ogg
    """
    if not file.content_type.startswith("audio/"):
        # Allow video/webm as it often contains audio from browser recording
        if not file.content_type.startswith("video/webm"):
             raise HTTPException(status_code=400, detail="Invalid file type. Please upload audio.")

    try:
        content = await file.read()
        
        # Limit size (e.g., 10MB)
        if len(content) > 10 * 1024 * 1024:
             raise HTTPException(status_code=413, detail="File too large (max 10MB)")
             
        text = await gemini_service.transcribe_audio(content, mime_type=file.content_type)
        return {"text": text}
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")
