from typing import Dict, Tuple, Optional, Any
from app.core.logging import get_logger
from app.models.schemas import ConversationState, LanguageCode, SessionContext
from app.services.translation_service import TranslationService
from app.services.speech_service import SpeechService
from app.services.bedrock_service import BedrockAgentService
from app.services.session_service import SessionManager
from app.services.google_services import GooglePlacesService, RideBookingAPIService
from app.core.exceptions import AIRideBookingException

logger = get_logger(__name__)


class ConversationService:
    """Main service orchestrating the conversation flow"""

    def __init__(self):
        self.translation_service = TranslationService()
        self.speech_service = SpeechService()
        self.bedrock_service = BedrockAgentService()
        self.session_manager = SessionManager()
        self.places_service = GooglePlacesService()
        self.ride_api_service = RideBookingAPIService()

    async def process_chat_message(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message through the complete pipeline

        Args:
            message: User's text message
            session_id: Optional session ID

        Returns:
            Response with text, session info, and ride details
        """
        try:
            # Create session if not provided
            if not session_id:
                session_id = await self.session_manager.create_session()

            # Get session context
            session_context = await self.session_manager.get_session(session_id)
            if not session_context:
                # Create new session if not found
                session_id = await self.session_manager.create_session()
                session_context = await self.session_manager.get_session(session_id)

            logger.info(f"Processing chat message for session {session_id}: {message}")

            # Step 1: Detect language and translate if needed
            detected_language = await self.translation_service.detect_language(message)
            english_text, _ = await self.translation_service.translate_if_needed(
                message, detected_language, to_english=True
            )

            # Step 2: Process with conversation logic
            response_text, updated_context = await self._process_conversation_logic(
                english_text, session_context
            )

            # Step 3: Translate response back if needed
            final_response, _ = await self.translation_service.translate_if_needed(
                response_text, detected_language, to_english=False
            )

            # Step 4: Update session
            await self.session_manager.add_conversation_entry(
                session_id, message, final_response
            )

            # Step 5: Extend session TTL
            await self.session_manager.extend_session(session_id)

            return {
                'response': final_response,
                'session_id': session_id,
                'detected_language': detected_language,
                'conversation_state': updated_context.state,
                'ride_details': updated_context.ride_details,
                'next_action': self._get_next_action(updated_context)
            }

        except Exception as e:
            logger.error(f"Chat message processing failed: {str(e)}")
            raise AIRideBookingException(f"Chat processing failed: {str(e)}")

    async def process_voice_input(
        self,
        audio_file_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process voice input through the complete pipeline

        Args:
            audio_file_path: Path to the audio file
            session_id: Optional session ID

        Returns:
            Response with text, audio, session info, and ride details
        """
        try:
            # Create session if not provided
            if not session_id:
                session_id = await self.session_manager.create_session()

            logger.info(f"Processing voice input for session {session_id}")

            # Step 1: Speech to text
            transcribed_text, detected_language = await self.speech_service.speech_to_text(
                audio_file_path
            )

            # Step 2: Translate if needed
            english_text, _ = await self.translation_service.translate_if_needed(
                transcribed_text, detected_language, to_english=True
            )

            # Step 3: Get session context
            session_context = await self.session_manager.get_session(session_id)
            if not session_context:
                session_id = await self.session_manager.create_session()
                session_context = await self.session_manager.get_session(session_id)

            # Step 4: Process with conversation logic
            response_text, updated_context = await self._process_conversation_logic(
                english_text, session_context
            )

            # Step 5: Translate response back if needed
            final_response, _ = await self.translation_service.translate_if_needed(
                response_text, detected_language, to_english=False
            )

            # Step 6: Convert response to speech
            audio_response_path = await self.speech_service.text_to_speech(
                final_response, detected_language
            )

            # Step 7: Update session
            await self.session_manager.add_conversation_entry(
                session_id, transcribed_text, final_response
            )

            # Step 8: Extend session TTL
            await self.session_manager.extend_session(session_id)

            return {
                'text_response': final_response,
                'audio_response_path': audio_response_path,
                'session_id': session_id,
                'detected_language': detected_language,
                'original_text': transcribed_text,
                'conversation_state': updated_context.state,
                'ride_details': updated_context.ride_details
            }

        except Exception as e:
            logger.error(f"Voice input processing failed: {str(e)}")
            raise AIRideBookingException(f"Voice processing failed: {str(e)}")

    async def _process_conversation_logic(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Tuple[str, SessionContext]:
        """
        Process conversation logic based on current state

        Args:
            user_input: User's input (in English)
            session_context: Current session context

        Returns:
            Tuple of (response_text, updated_session_context)
        """
        try:
            current_state = session_context.state

            logger.info(f"Processing conversation logic for state: {current_state}")

            # Handle different conversation states
            if current_state == ConversationState.GREETING:
                return await self._handle_greeting(user_input, session_context)

            elif current_state == ConversationState.ASKING_PICKUP:
                return await self._handle_pickup_location(user_input, session_context)

            elif current_state == ConversationState.ASKING_DROP:
                return await self._handle_drop_location(user_input, session_context)

            elif current_state == ConversationState.ASKING_PHONE:
                return await self._handle_phone_number(user_input, session_context)

            elif current_state == ConversationState.CONFIRMING_RIDE:
                return await self._handle_ride_confirmation(user_input, session_context)

            elif current_state == ConversationState.RIDE_CREATED:
                return await self._handle_post_ride_actions(user_input, session_context)

            else:
                # Default fallback
                return await self._handle_greeting(user_input, session_context)

        except Exception as e:
            logger.error(f"Conversation logic processing failed: {str(e)}")
            return "I'm sorry, I encountered an error. Please try again.", session_context

    async def _handle_greeting(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Tuple[str, SessionContext]:
        """Handle initial greeting and start ride booking flow"""
        try:
            # Update state to asking for pickup
            await self.session_manager.set_conversation_state(
                session_context.session_id,
                ConversationState.ASKING_PICKUP
            )

            # Update session context
            session_context.state = ConversationState.ASKING_PICKUP

            response = "Hello! I help with auto ride booking. What is your pickup location?"
            return response, session_context

        except Exception as e:
            logger.error(f"Greeting handling failed: {str(e)}")
            return "Hello! How can I help you with ride booking?", session_context

    async def _handle_pickup_location(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Tuple[str, SessionContext]:
        """Handle pickup location input"""
        try:
            # Resolve location using Google Places
            location_data = await self.places_service.resolve_location(user_input)

            if not location_data:
                return "I couldn't find that pickup location. Please try again with a more specific address.", session_context

            # Save pickup location
            await self.session_manager.set_location_data(
                session_context.session_id,
                'pickup_location',
                location_data
            )

            # Update state
            await self.session_manager.set_conversation_state(
                session_context.session_id,
                ConversationState.ASKING_DROP
            )

            # Update session context
            session_context.pickup_location = location_data
            session_context.state = ConversationState.ASKING_DROP

            response = f"Great! Pickup location set to {location_data['address']}. What is your drop location?"
            return response, session_context

        except Exception as e:
            logger.error(f"Pickup location handling failed: {str(e)}")
            return "Sorry, I couldn't process that pickup location. Please try again.", session_context

    async def _handle_drop_location(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Tuple[str, SessionContext]:
        """Handle drop location input"""
        try:
            # Resolve location using Google Places
            location_data = await self.places_service.resolve_location(user_input)

            if not location_data:
                return "I couldn't find that drop location. Please try again with a more specific address.", session_context

            # Save drop location
            await self.session_manager.set_location_data(
                session_context.session_id,
                'drop_location',
                location_data
            )

            # Update state
            await self.session_manager.set_conversation_state(
                session_context.session_id,
                ConversationState.ASKING_PHONE
            )

            # Update session context
            session_context.drop_location = location_data
            session_context.state = ConversationState.ASKING_PHONE

            response = f"Perfect! Drop location set to {location_data['address']}. Please provide your phone number so the driver can contact you."
            return response, session_context

        except Exception as e:
            logger.error(f"Drop location handling failed: {str(e)}")
            return "Sorry, I couldn't process that drop location. Please try again.", session_context

    async def _handle_phone_number(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Tuple[str, SessionContext]:
        """Handle phone number input"""
        try:
            # Extract phone number (simple validation)
            phone_number = ''.join(filter(str.isdigit, user_input))

            if len(phone_number) < 10:
                return "Please provide a valid 10-digit phone number.", session_context

            # Take last 10 digits if more than 10
            phone_number = phone_number[-10:]

            # Save phone number
            await self.session_manager.set_phone_number(
                session_context.session_id,
                phone_number
            )

            # Update session context
            session_context.phone_number = phone_number

            # Create ride booking
            ride_result = await self._create_ride_booking(session_context)

            if ride_result['success']:
                # Update state
                await self.session_manager.set_conversation_state(
                    session_context.session_id,
                    ConversationState.RIDE_CREATED
                )

                session_context.state = ConversationState.RIDE_CREATED
                session_context.ride_details = ride_result['ride_details']

                response = f"Ride request sent successfully! Ride ID: {ride_result['ride_id']}. Driver will call you in 5 minutes."
                return response, session_context
            else:
                response = f"Sorry, failed to create ride booking: {ride_result['error']}. Please try again."
                return response, session_context

        except Exception as e:
            logger.error(f"Phone number handling failed: {str(e)}")
            return "Sorry, I couldn't process your phone number. Please try again.", session_context

    async def _handle_ride_confirmation(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Tuple[str, SessionContext]:
        """Handle ride confirmation"""
        # This state is mainly for explicit confirmation flows
        return await self._handle_phone_number(user_input, session_context)

    async def _handle_post_ride_actions(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Tuple[str, SessionContext]:
        """Handle actions after ride is created"""
        try:
            user_input_lower = user_input.lower()

            if 'status' in user_input_lower or 'driver' in user_input_lower:
                # Get ride status
                if session_context.ride_details and session_context.ride_details.get('ride_id'):
                    status_result = await self.ride_api_service.get_ride_status(
                        session_context.ride_details['ride_id']
                    )

                    if status_result['success']:
                        driver_info = status_result['data'].get('driver', {})
                        response = f"Driver Name: {driver_info.get('name', 'Not assigned')}, Phone: {driver_info.get('phone', 'Not available')}"
                        return response, session_context

            elif 'cancel' in user_input_lower:
                # Cancel ride
                if session_context.ride_details and session_context.ride_details.get('ride_id'):
                    cancel_result = await self.ride_api_service.cancel_ride(
                        session_context.ride_details['ride_id']
                    )

                    if cancel_result['success']:
                        response = "Your ride has been cancelled."
                        # Reset session state
                        await self.session_manager.set_conversation_state(
                            session_context.session_id,
                            ConversationState.GREETING
                        )
                        session_context.state = ConversationState.GREETING
                        return response, session_context

            elif 'new' in user_input_lower or 'another' in user_input_lower:
                # Start new booking
                await self.session_manager.set_conversation_state(
                    session_context.session_id,
                    ConversationState.ASKING_PICKUP
                )
                session_context.state = ConversationState.ASKING_PICKUP
                response = "Sure! What is your pickup location for the new ride?"
                return response, session_context

            # Default response for post-ride state
            response = "Your ride is confirmed. You can ask for 'status', 'cancel' the ride, or book a 'new' ride."
            return response, session_context

        except Exception as e:
            logger.error(f"Post-ride action handling failed: {str(e)}")
            return "How else can I help you with your ride?", session_context

    async def _create_ride_booking(self, session_context: SessionContext) -> Dict[str, Any]:
        """Create ride booking using the external API"""
        try:
            if not all([
                session_context.pickup_location,
                session_context.drop_location,
                session_context.phone_number
            ]):
                return {
                    'success': False,
                    'error': 'Missing required booking information'
                }

            # Create ride via API
            result = await self.ride_api_service.create_ride(
                phone_number=session_context.phone_number,
                pickup_location=session_context.pickup_location,
                drop_location=session_context.drop_location
            )

            if result['success']:
                ride_details = {
                    'ride_id': result['ride_id'],
                    'message': result['message'],
                    'pickup_location': session_context.pickup_location,
                    'drop_location': session_context.drop_location,
                    'phone_number': session_context.phone_number
                }

                # Save ride details to session
                await self.session_manager.set_ride_details(
                    session_context.session_id,
                    ride_details
                )

                return {
                    'success': True,
                    'ride_id': result['ride_id'],
                    'ride_details': ride_details
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }

        except Exception as e:
            logger.error(f"Ride booking creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_next_action(self, session_context: SessionContext) -> Optional[str]:
        """Get the next expected action based on conversation state"""
        state_actions = {
            ConversationState.GREETING: "provide_greeting",
            ConversationState.ASKING_PICKUP: "provide_pickup_location",
            ConversationState.ASKING_DROP: "provide_drop_location",
            ConversationState.ASKING_PHONE: "provide_phone_number",
            ConversationState.CONFIRMING_RIDE: "confirm_ride",
            ConversationState.RIDE_CREATED: "ride_management",
            ConversationState.COMPLETED: "new_booking"
        }

        return state_actions.get(session_context.state)