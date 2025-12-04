"""
LegalHub Backend - Main FastAPI Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import sys

from app.config import settings
from app.api.routes import (
    auth,
    users,
    chat,
    cases,
    articles,
    bookings,
    lawyers,
    analytics,
)
from app.api.routes import debug

# Try to import AI/RAG features - make them optional
AI_FEATURES_AVAILABLE = False
try:
    from app.api.routes import rag, rag_scraper
    from app.services.rag_scheduler import initialize_scheduler, shutdown_scheduler
    AI_FEATURES_AVAILABLE = True
    print("✓ AI/RAG features enabled")
except ImportError as e:
    print(f"⚠️  AI/RAG features disabled - missing dependencies: {e}")
    print("   Install requirements-ai.txt to enable AI features")
    # Create dummy functions for scheduler
    async def initialize_scheduler():
        pass
    def shutdown_scheduler():
        pass


# Define lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for startup and shutdown events"""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Dev mode: {settings.DEV_MODE}")

    # Initialize Firebase (already done in firebase_service)
    from app.services.firebase_service import firebase_service
    from app.services.firebase_mcp_client import FirebaseMcpClient

    print("Firebase initialized")

    # Initialize FirebaseMcpClient
    global firebase_mcp_client
    firebase_mcp_client = FirebaseMcpClient(firebase_service)
    print("Firebase MCP Client initialized")

    # Initialize RAG Scheduler (only if AI features available)
    if AI_FEATURES_AVAILABLE:
        try:
            await initialize_scheduler()
            print("RAG Scheduler initialized")
        except Exception as e:
            print(f"Warning: RAG Scheduler initialization failed: {e}")
    else:
        print("Skipping RAG Scheduler initialization (AI features disabled)")

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")
    if AI_FEATURES_AVAILABLE:
        shutdown_scheduler()
        print("RAG Scheduler shutdown complete")


# Create FastAPI application with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=f"LegalHub Backend API - Democratizing access to legal services{' (AI Features Enabled)' if AI_FEATURES_AVAILABLE else ''}",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


# Include core routers (always available)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(cases.router)
app.include_router(articles.router)
app.include_router(bookings.router)
app.include_router(lawyers.router)
app.include_router(analytics.router)

# Include AI/RAG routers only if available
if AI_FEATURES_AVAILABLE:
    app.include_router(rag.router)
    app.include_router(rag_scraper.router)

# Include debug router in debug mode
if settings.DEBUG:
    app.include_router(debug.router)


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Welcome to LegalHub API",
        "ai_features": AI_FEATURES_AVAILABLE,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "firebase_configured": bool(settings.FIREBASE_CREDENTIALS_PATH),
        "gemini_configured": bool(settings.GOOGLE_API_KEY),
        "features": {
            "authentication": True,
            "bookings": True,
            "cases": True,
            "lawyers": True,
            "chat": True,
            "analytics": True,
            "ai_rag": AI_FEATURES_AVAILABLE,
            "web_scraping": AI_FEATURES_AVAILABLE,
        }
    }


@app.get("/api/features", tags=["Health"])
async def get_features():
    """Get available API features"""
    return {
        "core_features": [
            "authentication",
            "user_management",
            "lawyer_bookings",
            "case_reporting",
            "chat_messaging",
            "analytics",
        ],
        "ai_features": [
            "rag_chatbot",
            "web_scraping",
            "document_embeddings",
        ] if AI_FEATURES_AVAILABLE else [],
        "ai_enabled": AI_FEATURES_AVAILABLE,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
