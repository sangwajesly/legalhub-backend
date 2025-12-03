"""
LegalHub Backend - Main FastAPI Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

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
    rag,
    rag_scraper,
)
from app.api.routes import debug


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
    from app.services.rag_scheduler import initialize_scheduler, shutdown_scheduler

    print("Firebase initialized")

    # Initialize FirebaseMcpClient
    global firebase_mcp_client
    firebase_mcp_client = FirebaseMcpClient(firebase_service)
    print("Firebase MCP Client initialized")

    # Initialize RAG Scheduler
    # Note: If running for the first time, the SentenceTransformer model used by the RAG system
    # (e.g., 'all-MiniLM-L6-v2') will be downloaded. This requires internet access.
    # Ensure Firebase and Gemini services are properly configured as well.
    await initialize_scheduler()
    print("RAG Scheduler initialized")

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")
    shutdown_scheduler()
    print("RAG Scheduler shutdown complete")


# Create FastAPI application with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LegalHub Backend API - Democratizing access to legal services",
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


# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(cases.router)
app.include_router(articles.router)
app.include_router(bookings.router)
app.include_router(lawyers.router)
app.include_router(analytics.router)
app.include_router(rag.router)
app.include_router(rag_scraper.router)
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
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
