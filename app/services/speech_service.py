import asyncio
import tempfile
import os
from typing import Optional, Tuple
from pathlib import Path
import openai
from google.cloud import texttospeech
from app.core.exceptions import SpeechProcessingException
from app.core.logging import get_logger
from config.settings import get_settings, LANGUAGE_VOICE_MAP

logger = get_logger(__name__)


class SpeechService:
    """OpenAI Whisper + Google TTS for speech processing"""

    def __init__(self):
        self.settings = get_settings()
        try:
            # Initialize OpenAI client for Whisper
            self.openai_client = openai.OpenAI(
                api_key=self.settings.openai_api_key
            )

            # Initialize Google TTS client
            self.tts_client = texttospeech.TextToSpeechClient()

            logger.info("Speech service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize speech service: {str(e)}")
            raise SpeechProcessingException(f"Speech service initialization failed: {str(e)}")

    async def speech_to_text(self, audio_file_path: str) -> Tuple[str, str]:
        """
        Convert speech to text using OpenAI Whisper

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        try:
            if not os.path.exists(audio_file_path):
                raise SpeechProcessingException(f"Audio file not found: {audio_file_path}")

            logger.info(f"Processing audio file: {audio_file_path}")

            with open(audio_file_path, "rb") as audio_file:
                # Use Whisper for transcription with language detection
                transcript_response = await asyncio.to_thread(
                    self.openai_client.audio.transcriptions.create,
                    model=self.settings.openai_model,
                    file=audio_file,
                    language=None,  # Auto-detect language
                    response_format="verbose_json"
                )

            transcribed_text = transcript_response.text
            detected_language = getattr(transcript_response, 'language', 'en')

            # Map ISO language codes to our supported languages
            language_map = {
                'en': 'en',
                'ta': 'ta',
                'ml': 'ml',
                'english': 'en',
                'tamil': 'ta',
                'malayalam': 'ml'
            }

            normalized_language = language_map.get(detected_language.lower(), 'en')

            logger.info(f"Speech-to-text completed: '{transcribed_text}' (language: {normalized_language})")
            return transcribed_text, normalized_language

        except Exception as e:
            logger.error(f"Speech-to-text conversion failed: {str(e)}")
            raise SpeechProcessingException(f"Speech-to-text failed: {str(e)}")

    async def text_to_speech(
        self,
        text: str,
        language_code: str = "en",
        output_path: Optional[str] = None
    ) -> str:
        """
        Convert text to speech using Google TTS

        Args:
            text: Text to convert to speech
            language_code: Language code (en, ta, ml)
            output_path: Optional output file path

        Returns:
            Path to the generated audio file
        """
        try:
            # Map language code to Google TTS language code
            tts_language_code = LANGUAGE_VOICE_MAP.get(language_code, "en-US")

            # Create synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=tts_language_code,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            )

            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.settings.tts_voice_speed,
            )

            # Generate speech
            response = await asyncio.to_thread(
                self.tts_client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            # Save audio to file
            if not output_path:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f".{self.settings.audio_format}",
                    prefix="tts_"
                )
                output_path = temp_file.name
                temp_file.close()

            with open(output_path, "wb") as audio_file:
                audio_file.write(response.audio_content)

            logger.info(f"Text-to-speech completed: '{text}' -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Text-to-speech conversion failed: {str(e)}")
            raise SpeechProcessingException(f"Text-to-speech failed: {str(e)}")

    async def process_audio_file(self, audio_file_path: str) -> Tuple[str, str]:
        """
        Process uploaded audio file through speech-to-text

        Args:
            audio_file_path: Path to uploaded audio file

        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        try:
            # Validate file exists and is readable
            if not os.path.exists(audio_file_path):
                raise SpeechProcessingException(f"Audio file not found: {audio_file_path}")

            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                raise SpeechProcessingException("Audio file is empty")

            if file_size > 25 * 1024 * 1024:  # 25MB limit for OpenAI Whisper
                raise SpeechProcessingException("Audio file too large (max 25MB)")

            # Process the audio
            return await self.speech_to_text(audio_file_path)

        except Exception as e:
            logger.error(f"Audio file processing failed: {str(e)}")
            raise SpeechProcessingException(f"Audio processing failed: {str(e)}")

    async def cleanup_temp_files(self, *file_paths: str) -> None:
        """Clean up temporary audio files"""
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")

    def get_supported_audio_formats(self) -> list:
        """Get list of supported audio formats"""
        return [
            "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "flac"
        ]