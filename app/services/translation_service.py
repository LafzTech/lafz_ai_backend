import asyncio
from typing import Optional, Tuple
from google.cloud import translate_v2 as translate
from app.core.exceptions import TranslationException
from app.core.logging import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class TranslationService:
    """Google Cloud Translation Service for Tamil, Malayalam, and English"""

    def __init__(self):
        self.settings = get_settings()
        try:
            self.translate_client = translate.Client()
            logger.info("Translation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize translation service: {str(e)}")
            raise TranslationException(f"Translation service initialization failed: {str(e)}")

    async def detect_language(self, text: str) -> str:
        """Detect language of the input text"""
        try:
            result = await asyncio.to_thread(
                self.translate_client.detect_language, text
            )
            detected_lang = result['language']
            confidence = result.get('confidence', 0)

            logger.info(f"Detected language: {detected_lang} (confidence: {confidence})")

            # Map detected languages to our supported languages
            language_map = {
                'ta': 'ta',  # Tamil
                'ml': 'ml',  # Malayalam
                'en': 'en',  # English
            }

            return language_map.get(detected_lang, 'en')  # Default to English

        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            # Default to English if detection fails
            return 'en'

    async def translate_to_english(self, text: str, source_language: str) -> str:
        """Translate Tamil/Malayalam text to English"""
        if source_language == 'en':
            return text

        try:
            result = await asyncio.to_thread(
                self.translate_client.translate,
                text,
                source_language=source_language,
                target_language='en'
            )

            translated_text = result['translatedText']
            logger.info(f"Translated to English: '{text}' -> '{translated_text}'")
            return translated_text

        except Exception as e:
            logger.error(f"Translation to English failed: {str(e)}")
            raise TranslationException(f"Failed to translate to English: {str(e)}")

    async def translate_from_english(self, text: str, target_language: str) -> str:
        """Translate English text to Tamil/Malayalam"""
        if target_language == 'en':
            return text

        try:
            result = await asyncio.to_thread(
                self.translate_client.translate,
                text,
                source_language='en',
                target_language=target_language
            )

            translated_text = result['translatedText']
            logger.info(f"Translated from English: '{text}' -> '{translated_text}'")
            return translated_text

        except Exception as e:
            logger.error(f"Translation from English failed: {str(e)}")
            raise TranslationException(f"Failed to translate from English: {str(e)}")

    async def translate_if_needed(
        self,
        text: str,
        detected_language: str,
        to_english: bool = True
    ) -> Tuple[str, str]:
        """
        Translate text if needed based on detected language

        Args:
            text: Input text
            detected_language: Detected language code
            to_english: If True, translate to English; if False, translate from English

        Returns:
            Tuple of (translated_text, language_used)
        """
        try:
            if to_english:
                if detected_language in ['ta', 'ml']:
                    translated = await self.translate_to_english(text, detected_language)
                    return translated, detected_language
                else:
                    return text, 'en'
            else:
                if detected_language in ['ta', 'ml']:
                    translated = await self.translate_from_english(text, detected_language)
                    return translated, detected_language
                else:
                    return text, 'en'

        except Exception as e:
            logger.error(f"Translation process failed: {str(e)}")
            # Return original text if translation fails
            return text, detected_language