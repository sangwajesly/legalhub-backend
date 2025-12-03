"""
Configuration settings for LegalHub Backend
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Server Configuration
    APP_NAME: str = "LegalHub Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"
    FIREBASE_STORAGE_BUCKET: str = ""
    FIREBASE_EMULATOR_HOST: str = ""
    DEV_MODE: bool = False

    # Google Gemini API
    GOOGLE_API_KEY: str = "AIzaSyC5mJNpSkdmp7jZBp2NwWjJjzzZILIkjjk"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_URL: str = (
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    )
    DEBUG_MOCK_GEMINI: bool = False

    # JWT Configuration
    JWT_SECRET_KEY: str = "your_super_secret_jwt_key_change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3001,http://localhost:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""

    # Email Configuration (Optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@legalhub.com"

    # ChromaDB Configuration
    CHROMADB_PATH: str = "./chroma_db"

    # RAG Scheduler Configuration
    RAG_SCRAPE_INTERVAL_HOURS: int = 72  # Scrape every 72 hours
    RAG_SCRAPE_ENABLED: bool = True  # Enable/disable automatic scraping
    RAG_SCRAPE_ON_STARTUP: bool = False  # Run scraper immediately on startup

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "allow"}


# Global settings instance
settings = Settings()
