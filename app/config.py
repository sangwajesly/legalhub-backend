from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    APP_NAME: str = "LegalHub Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Firebase
    FIREBASE_CREDENTIALS_PATH: Optional[str] = "./firebase-credentials.json"
    FIREBASE_STORAGE_BUCKET: Optional[str] = None
    FIREBASE_EMULATOR_HOST: Optional[str] = None

    # Google Gemini API
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    GEMINI_API_URL: Optional[str] = None

    # Auth
    JWT_SECRET_KEY: str = "supersecretdev"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Dev toggles
    DEV_MODE: bool = True
    DEBUG_MOCK_GEMINI: bool = True

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None

    # Email Configuration (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # Payment Gateway (Optional)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None



settings = Settings()
