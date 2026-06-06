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
    BACKEND_URL: str = "http://localhost:8001"

    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"
    # Support for raw JSON credentials (env var)
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_STORAGE_BUCKET: str = "legahub-70645.appspot.com"
    FIREBASE_EMULATOR_HOST: str = ""
    DEV_MODE: bool = False

    # Google Gemini API
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    # Ordered list of Gemini models to try before falling back to other providers.
    # The primary GEMINI_MODEL is always tried first automatically.
    GEMINI_FALLBACK_MODELS: str = "gemini-2.0-flash,gemini-1.5-flash,gemini-1.5-pro"
    GEMINI_API_URL: str = (
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    )
    DEBUG_MOCK_GEMINI: bool = False

    # Fallback AI provider configuration
    FALLBACK_AI_PROVIDERS: str = "huggingface,openai,cohere,groq,grok"
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_API_URL: str = ""
    HUGGINGFACE_MODEL: str = "google/flan-t5-small"
    OPENAI_API_KEY: str = ""
    OPENAI_API_URL: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    COHERE_API_KEY: str = ""
    COHERE_API_URL: str = ""
    COHERE_MODEL: str = "command-xlarge-nightly"
    GROQ_API_KEY: str = ""
    GROQ_API_URL: str = ""
    GROQ_MODEL: str = "groq-1-small"
    GROK_API_KEY: str = ""
    GROK_API_URL: str = ""
    GROK_MODEL: str = "grok-1"

    # JWT Configuration
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration - Allow all localhost ports in development
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:5173,"
        "https://legalhubeasy.vercel.app"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        origins = [origin.strip()
                   for origin in self.ALLOWED_ORIGINS.split(",")]
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
    # Hybrid backend support: use a hosted vector database when enabled,
    # otherwise fall back to local FAISS files for offline operation.
    USE_REMOTE_VECTOR_STORE: bool = False
    VECTOR_STORE_TYPE: str = "local"  # local | pinecone
    VECTOR_STORE_REMOTE_URL: str = ""
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = "legalhub_documents"
    PINECONE_METRIC: str = "cosine"

    model_config = {"env_file": ".env",
                    "case_sensitive": True, "extra": "allow"}


# Global settings instance
settings = Settings()
