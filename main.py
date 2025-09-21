from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from app.api.endpoints import router
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import AIRideBookingException
from app.services.session_service import SessionManager
from config.settings import get_settings

# Get settings
settings = get_settings()

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global session manager for cleanup
session_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global session_manager

    # Startup
    logger.info("Starting AI Ride Booking System...")

    try:
        # Initialize session manager
        session_manager = SessionManager()

        # Test Redis connection
        test_session = await session_manager.create_session("test_user")
        await session_manager.delete_session(test_session)

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Ride Booking System...")

    try:
        # Cleanup session manager
        if session_manager:
            await session_manager.close()

        logger.info("Application shutdown completed successfully")

    except Exception as e:
        logger.error(f"Application shutdown error: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AI-Powered Ride Booking System

    A multilingual (English, Tamil, Malayalam) ride booking service with:
    - Voice conversation support (OpenAI Whisper + Google TTS)
    - Text chat support
    - Real-time translation (Google Cloud Translation)
    - Intelligent conversation management (AWS Bedrock + Claude 3 Haiku)
    - Location resolution (Google Places API)
    - Session management (Redis)

    ## Supported Languages
    - English (en)
    - Tamil (ta)
    - Malayalam (ml)

    ## Features
    - Speech-to-text and text-to-speech
    - Location autocomplete and resolution
    - Ride booking with external API integration
    - Session-based conversation management
    - Real-time ride status and driver information
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware for production security
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )

# Include API routes
app.include_router(router, prefix="/api", tags=["AI Ride Booking"])


# Global exception handlers
@app.exception_handler(AIRideBookingException)
async def ai_ride_booking_exception_handler(request, exc: AIRideBookingException):
    """Handle custom AI ride booking exceptions"""
    logger.error(f"AI service error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "error_code": exc.error_code or "AI_SERVICE_ERROR"
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors"""
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "error": str(exc),
            "error_code": "VALIDATION_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests"""
    start_time = asyncio.get_event_loop().time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = asyncio.get_event_loop().time() - start_time

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    return response


# Health check for load balancers
@app.get("/ping")
async def ping():
    """Simple ping endpoint for health checks"""
    return {"status": "ok"}


# Application info
@app.get("/info")
async def app_info():
    """Application information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
        "supported_languages": settings.supported_languages,
        "features": [
            "Voice conversation",
            "Text chat",
            "Multilingual support",
            "Real-time translation",
            "Location resolution",
            "Ride booking",
            "Session management"
        ]
    }


# CLI runner
def run_server():
    """Run the FastAPI server"""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    run_server()