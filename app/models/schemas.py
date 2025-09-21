from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class LanguageCode(str, Enum):
    ENGLISH = "en"
    TAMIL = "ta"
    MALAYALAM = "ml"


class RideStatus(str, Enum):
    PENDING = "pending"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_ARRIVING = "driver_arriving"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConversationState(str, Enum):
    GREETING = "greeting"
    ASKING_PICKUP = "asking_pickup"
    ASKING_DROP = "asking_drop"
    ASKING_PHONE = "asking_phone"
    CONFIRMING_RIDE = "confirming_ride"
    RIDE_CREATED = "ride_created"
    COMPLETED = "completed"


# Request Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    language: Optional[LanguageCode] = LanguageCode.ENGLISH

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, I need a ride",
                "session_id": "session_123",
                "language": "en"
            }
        }


class VoiceRequest(BaseModel):
    audio_file_path: str = Field(..., description="Path to the uploaded audio file")
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "audio_file_path": "/tmp/audio_123.mp3",
                "session_id": "session_123"
            }
        }


# Response Models
class LocationData(BaseModel):
    address: str
    coordinates: Dict[str, float] = Field(..., description="Latitude and longitude")
    place_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "address": "Ukkadam, Coimbatore, Tamil Nadu 641001, India",
                "coordinates": {"lat": 10.9902127, "lng": 76.96286580000002},
                "place_id": "ChIJ123456789"
            }
        }


class DriverInfo(BaseModel):
    name: str
    phone: str
    vehicle_number: str
    rating: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Raja",
                "phone": "3698521470",
                "vehicle_number": "TN 01 AB 1234",
                "rating": 4.5
            }
        }


class RideDetails(BaseModel):
    ride_id: Optional[int] = None
    pickup_location: Optional[LocationData] = None
    drop_location: Optional[LocationData] = None
    phone_number: Optional[str] = None
    status: Optional[RideStatus] = None
    driver: Optional[DriverInfo] = None
    eta: Optional[str] = None
    distance: Optional[str] = None
    duration: Optional[str] = None
    fare: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "ride_id": 123456,
                "pickup_location": {
                    "address": "Ukkadam, Coimbatore",
                    "coordinates": {"lat": 10.9902127, "lng": 76.96286580000002}
                },
                "drop_location": {
                    "address": "Gandhipuram, Tamil Nadu",
                    "coordinates": {"lat": 11.0175845, "lng": 76.9674075}
                },
                "phone_number": "1234567890",
                "status": "driver_assigned",
                "eta": "5 minutes"
            }
        }


class ChatResponse(BaseModel):
    response: str
    session_id: str
    detected_language: LanguageCode
    ride_details: Optional[RideDetails] = None
    next_action: Optional[str] = None
    conversation_state: ConversationState

    class Config:
        json_schema_extra = {
            "example": {
                "response": "What is your pickup location?",
                "session_id": "session_123",
                "detected_language": "en",
                "conversation_state": "asking_pickup"
            }
        }


class VoiceResponse(BaseModel):
    text_response: str
    audio_response_url: Optional[str] = None
    session_id: str
    detected_language: LanguageCode
    ride_details: Optional[RideDetails] = None
    conversation_state: ConversationState

    class Config:
        json_schema_extra = {
            "example": {
                "text_response": "What is your pickup location?",
                "audio_response_url": "https://storage.example.com/audio/response_123.mp3",
                "session_id": "session_123",
                "detected_language": "en",
                "conversation_state": "asking_pickup"
            }
        }


# Session Models
class SessionContext(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    state: ConversationState = ConversationState.GREETING
    language: LanguageCode = LanguageCode.ENGLISH
    pickup_location: Optional[LocationData] = None
    drop_location: Optional[LocationData] = None
    phone_number: Optional[str] = None
    ride_details: Optional[RideDetails] = None
    created_at: datetime
    updated_at: datetime
    conversation_history: List[Dict[str, Any]] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# API Integration Models
class RideCreationPayload(BaseModel):
    phone_code: str = "+91"
    phone_number: str
    origin_latitude: float
    origin_longitude: float
    destination_latitude: float
    destination_longitude: float
    pickup_location: str
    drop_location: str
    distance: str = "N/A"
    duration: str = "N/A"

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "phone_code": "+91",
                "phone_number": "1234567890",
                "origin_latitude": 10.9902127,
                "origin_longitude": 76.96286580000002,
                "destination_latitude": 11.0175845,
                "destination_longitude": 76.9674075,
                "pickup_location": "Ukkadam, Coimbatore, Tamil Nadu 641001, India",
                "drop_location": "Gandhipuram, Tamil Nadu 641012, India"
            }
        }


class RideCreationResponse(BaseModel):
    ride_id: int
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "ride_id": 123456,
                "message": "Ride created successfully"
            }
        }


# Error Models
class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid request",
                "details": "Missing required field: phone_number",
                "error_code": "VALIDATION_ERROR"
            }
        }


# Health Check Model
class HealthCheck(BaseModel):
    status: str = "healthy"
    service: str = "AI Ride Booking System"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }