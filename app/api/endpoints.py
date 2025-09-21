import tempfile
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional

from app.models.schemas import (
    ChatRequest, ChatResponse, VoiceResponse, HealthCheck,
    ErrorResponse, SessionContext, RideDetails
)
from app.services.conversation_service import ConversationService
from app.services.session_service import SessionManager
from app.services.google_services import RideBookingAPIService
from app.core.exceptions import AIRideBookingException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize services
conversation_service = ConversationService()
session_manager = SessionManager()
ride_api_service = RideBookingAPIService()

# Create router
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process chat message through the AI pipeline

    This endpoint handles text-based conversations for ride booking.
    It performs language detection, translation, conversation management,
    and returns appropriate responses.
    """
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")

        # Process the chat message
        result = await conversation_service.process_chat_message(
            message=request.message,
            session_id=request.session_id
        )

        return ChatResponse(
            response=result['response'],
            session_id=result['session_id'],
            detected_language=result['detected_language'],
            conversation_state=result['conversation_state'],
            ride_details=result.get('ride_details'),
            next_action=result.get('next_action')
        )

    except AIRideBookingException as e:
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in chat processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/voice", response_model=VoiceResponse)
async def process_voice(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Process voice input through the AI pipeline

    This endpoint handles voice-based conversations for ride booking.
    It performs speech-to-text, language detection, translation,
    conversation management, and text-to-speech conversion.
    """
    try:
        logger.info(f"Processing voice request: {audio_file.filename}")

        # Validate audio file
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.filename.split('.')[-1]}") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name

        try:
            # Process the voice input
            result = await conversation_service.process_voice_input(
                audio_file_path=temp_audio_path,
                session_id=session_id
            )

            # Schedule cleanup of temporary files
            background_tasks.add_task(cleanup_temp_files, temp_audio_path)

            return VoiceResponse(
                text_response=result['text_response'],
                audio_response_url=f"/audio/{os.path.basename(result['audio_response_path'])}",
                session_id=result['session_id'],
                detected_language=result['detected_language'],
                conversation_state=result['conversation_state'],
                ride_details=result.get('ride_details')
            )

        finally:
            # Immediate cleanup of input file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

    except AIRideBookingException as e:
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in voice processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/session/{session_id}", response_model=SessionContext)
async def get_session_status(session_id: str):
    """
    Get session status and context

    Returns the current state of a conversation session including
    conversation history, current state, and collected information.
    """
    try:
        logger.info(f"Getting session status: {session_id}")

        session_context = await session_manager.get_session(session_id)

        if not session_context:
            raise HTTPException(status_code=404, detail="Session not found")

        return session_context

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/session/{session_id}/extend")
async def extend_session(session_id: str):
    """
    Extend session TTL

    Extends the time-to-live for a session to prevent it from expiring.
    """
    try:
        logger.info(f"Extending session: {session_id}")

        success = await session_manager.extend_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session extended successfully", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session

    Removes a session and all associated data from the system.
    """
    try:
        logger.info(f"Deleting session: {session_id}")

        success = await session_manager.delete_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ride/{ride_id}/cancel")
async def cancel_ride(ride_id: int):
    """
    Cancel a ride booking

    Cancels an existing ride booking using the external ride API.
    """
    try:
        logger.info(f"Cancelling ride: {ride_id}")

        result = await ride_api_service.cancel_ride(ride_id)

        if result['success']:
            return {
                "message": "Ride cancelled successfully",
                "ride_id": ride_id
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Cancellation failed'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling ride: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ride/{ride_id}/status")
async def get_ride_status(ride_id: int):
    """
    Get ride status

    Retrieves the current status of a ride including driver information
    and estimated time of arrival.
    """
    try:
        logger.info(f"Getting ride status: {ride_id}")

        result = await ride_api_service.get_ride_status(ride_id)

        if result['success']:
            return result['data']
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Status check failed'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ride status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve generated audio files

    Returns audio files generated by the text-to-speech service.
    """
    try:
        # In production, you might want to store these in a proper file storage service
        audio_path = f"/tmp/{filename}"

        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")

        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint

    Returns the current health status of the AI ride booking system.
    """
    try:
        # You could add more comprehensive health checks here
        # like checking Redis connectivity, external API availability, etc.

        return HealthCheck(
            status="healthy",
            service="AI Ride Booking System",
            version="1.0.0"
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            service="AI Ride Booking System",
            version="1.0.0"
        )


@router.get("/")
async def root():
    """
    Root endpoint

    Basic information about the API.
    """
    return {
        "service": "AI Ride Booking System",
        "version": "1.0.0",
        "description": "Multilingual AI-powered ride booking with voice and chat support",
        "endpoints": {
            "chat": "/api/chat",
            "voice": "/api/voice",
            "health": "/api/health",
            "docs": "/docs"
        }
    }


# Background task functions
async def cleanup_temp_files(*file_paths: str):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")


# Error handlers
@router.exception_handler(AIRideBookingException)
async def ai_ride_booking_exception_handler(request, exc: AIRideBookingException):
    """Handle custom AI ride booking exceptions"""
    return ErrorResponse(
        error=exc.message,
        error_code=exc.error_code
    )


@router.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors"""
    return ErrorResponse(
        error=str(exc),
        error_code="VALIDATION_ERROR"
    )