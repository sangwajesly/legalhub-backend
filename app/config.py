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
    # Support for raw JSON credentials (env var)
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_STORAGE_BUCKET: str = ""
    FIREBASE_EMULATOR_HOST: str = ""
    DEV_MODE: bool = False

    # Google Gemini API
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_URL: str = (
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    )
    DEBUG_MOCK_GEMINI: bool = False

    # JWT Configuration
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration - Allow all localhost ports in development
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        origins = [origin.strip()
                   for origin in self.ALLOWED_ORIGINS.split(",")]
        # In development, explicitly add common localhost ports
        if self.DEBUG:
            # Add more localhost ports for development
            localhost_ports = [3000, 3001, 5173, 5000, 4200]
            for port in localhost_ports:
                origin = f"http://localhost:{port}"
                if origin not in origins:
                    origins.append(origin)
            # Also add 127.0.0.1 variants
            for port in localhost_ports:
                origin = f"http://127.0.0.1:{port}"
                if origin not in origins:
                    origins.append(origin)
        return origins

    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""

    # Email Configuration (Optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@legalhub.com"

    # Payment Settings
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    MTN_MOMO_API_KEY: str = ""
    MTN_MOMO_USER_ID: str = ""
    RAG_SCRAPE_INTERVAL_HOURS: int = 72  # Scrape every 72 hours
    RAG_SCRAPE_ENABLED: bool = True  # Enable/disable automatic scraping
    RAG_SCRAPE_ON_STARTUP: bool = False  # Run scraper immediately on startup

    # FAISS/Vector Store Configuration
    # Path for FAISS index storage (legacy name kept for compatibility)
    CHROMADB_PATH: str = "./chroma_db"

    model_config = {"env_file": ".env",
                    "case_sensitive": True, "extra": "allow"}


# Global settings instance
settings = Settings()
