import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class FileService:
    @staticmethod
    async def save_upload(file: UploadFile) -> str:
        """Save upload to local disk and return a unique file_id"""
        file_ext = Path(file.filename).suffix
        file_id = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / file_id
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return file_id

    @staticmethod
    def get_file_path(file_id: str) -> Path:
        """Get absolute path of a file"""
        path = UPLOAD_DIR / file_id
        if not path.exists():
            return None
        return path

    @staticmethod
    def get_file_content(file_id: str) -> bytes:
        """Read file content as bytes"""
        path = FileService.get_file_path(file_id)
        if path:
            return path.read_bytes()
        return None

file_service = FileService()
