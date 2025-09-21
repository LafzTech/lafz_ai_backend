import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application Settings
    app_name: str = "AI Ride Booking System"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str = "your-super-secret-key-change-this"
    access_token_expire_minutes: int = 30

    # Database & Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    session_ttl: int = 3600  # 1 hour

    # OpenAI Settings
    openai_api_key: str = ""
    openai_model: str = "whisper-1"

    # Google Cloud Settings
    google_cloud_project_id: str = ""
    google_application_credentials: str = ""
    google_maps_api_key: str = ""
    google_translate_api_key: str = ""

    # AWS Settings
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_bedrock_agent_id: str = ""
    aws_bedrock_agent_alias_id: str = ""
    aws_lambda_function_arn: str = ""

    # Ride Booking API
    ride_api_base_url: str = "http://192.168.1.2:8000"
    ride_api_timeout: int = 10

    # Language Settings
    supported_languages: list = ["en", "ta", "ml"]
    default_language: str = "en"

    # Voice Settings
    tts_voice_speed: float = 1.0
    audio_format: str = "mp3"

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Language mappings for TTS
LANGUAGE_VOICE_MAP = {
    "en": "en-US",
    "ta": "ta-IN",
    "ml": "ml-IN"
}

# Language codes for translation
LANGUAGE_CODES = {
    "english": "en",
    "tamil": "ta",
    "malayalam": "ml"
}

# API Endpoints
API_ENDPOINTS = {
    "create_ride": "/map/admin/create-admin-ride",
    "cancel_ride": "/map/admin/cancel-ride",
    "ride_status": "/map/admin/ride-status"
}