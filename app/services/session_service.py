import asyncio
import json
import uuid
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.exceptions import SessionException
from app.core.logging import get_logger
from app.models.schemas import SessionContext, ConversationState, LanguageCode
from config.settings import get_settings

logger = get_logger(__name__)


class SessionManager:
    """Redis-based session management for conversation state"""

    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        self.session_ttl = self.settings.session_ttl

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client connection"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.Redis(
                    host=self.settings.redis_host,
                    port=self.settings.redis_port,
                    password=self.settings.redis_password,
                    db=self.settings.redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )

                # Test connection
                await self.redis_client.ping()
                logger.info("Redis connection established successfully")

            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise SessionException(f"Redis connection failed: {str(e)}")

        return self.redis_client

    async def create_session(self, user_id: Optional[str] = None, language: LanguageCode = LanguageCode.ENGLISH) -> str:
        """
        Create a new conversation session

        Args:
            user_id: Optional user identifier
            language: Initial language for the session

        Returns:
            Session ID
        """
        try:
            # Generate unique session ID
            session_id = f"session_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"

            # Create initial session context
            now = datetime.now()
            session_context = SessionContext(
                session_id=session_id,
                user_id=user_id,
                state=ConversationState.GREETING,
                language=language,
                created_at=now,
                updated_at=now,
                conversation_history=[]
            )

            # Store in Redis
            redis_client = await self._get_redis_client()
            await redis_client.setex(
                session_id,
                self.session_ttl,
                session_context.model_dump_json()
            )

            logger.info(f"Created new session: {session_id} for user: {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise SessionException(f"Session creation failed: {str(e)}")

    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        Retrieve session context

        Args:
            session_id: Session identifier

        Returns:
            Session context or None if not found
        """
        try:
            redis_client = await self._get_redis_client()
            session_data = await redis_client.get(session_id)

            if not session_data:
                logger.warning(f"Session not found: {session_id}")
                return None

            # Parse and return session context
            session_dict = json.loads(session_data)
            session_context = SessionContext(**session_dict)

            logger.debug(f"Retrieved session: {session_id}")
            return session_context

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            raise SessionException(f"Session retrieval failed: {str(e)}")

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session context

        Args:
            session_id: Session identifier
            updates: Dictionary of updates to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            session_context = await self.get_session(session_id)

            if not session_context:
                logger.warning(f"Cannot update non-existent session: {session_id}")
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(session_context, key):
                    setattr(session_context, key, value)

            # Update timestamp
            session_context.updated_at = datetime.now()

            # Save back to Redis
            redis_client = await self._get_redis_client()
            await redis_client.setex(
                session_id,
                self.session_ttl,
                session_context.model_dump_json()
            )

            logger.debug(f"Updated session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {str(e)}")
            raise SessionException(f"Session update failed: {str(e)}")

    async def add_conversation_entry(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a conversation entry to session history

        Args:
            session_id: Session identifier
            user_message: User's message
            bot_response: Bot's response
            metadata: Optional metadata

        Returns:
            True if successful
        """
        try:
            session_context = await self.get_session(session_id)

            if not session_context:
                return False

            # Create conversation entry
            conversation_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_message': user_message,
                'bot_response': bot_response,
                'metadata': metadata or {}
            }

            # Add to conversation history
            session_context.conversation_history.append(conversation_entry)

            # Limit history size (keep last 50 entries)
            if len(session_context.conversation_history) > 50:
                session_context.conversation_history = session_context.conversation_history[-50:]

            # Update session
            return await self.update_session(session_id, {
                'conversation_history': session_context.conversation_history
            })

        except Exception as e:
            logger.error(f"Failed to add conversation entry: {str(e)}")
            return False

    async def set_conversation_state(self, session_id: str, state: ConversationState) -> bool:
        """
        Update conversation state

        Args:
            session_id: Session identifier
            state: New conversation state

        Returns:
            True if successful
        """
        try:
            return await self.update_session(session_id, {'state': state})

        except Exception as e:
            logger.error(f"Failed to set conversation state: {str(e)}")
            return False

    async def set_location_data(
        self,
        session_id: str,
        location_type: str,
        location_data: Dict
    ) -> bool:
        """
        Set pickup or drop location data

        Args:
            session_id: Session identifier
            location_type: 'pickup_location' or 'drop_location'
            location_data: Location information

        Returns:
            True if successful
        """
        try:
            if location_type not in ['pickup_location', 'drop_location']:
                raise ValueError("location_type must be 'pickup_location' or 'drop_location'")

            return await self.update_session(session_id, {location_type: location_data})

        except Exception as e:
            logger.error(f"Failed to set location data: {str(e)}")
            return False

    async def set_phone_number(self, session_id: str, phone_number: str) -> bool:
        """
        Set user's phone number

        Args:
            session_id: Session identifier
            phone_number: Phone number

        Returns:
            True if successful
        """
        try:
            return await self.update_session(session_id, {'phone_number': phone_number})

        except Exception as e:
            logger.error(f"Failed to set phone number: {str(e)}")
            return False

    async def set_ride_details(self, session_id: str, ride_details: Dict) -> bool:
        """
        Set ride booking details

        Args:
            session_id: Session identifier
            ride_details: Ride information

        Returns:
            True if successful
        """
        try:
            return await self.update_session(session_id, {'ride_details': ride_details})

        except Exception as e:
            logger.error(f"Failed to set ride details: {str(e)}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        try:
            redis_client = await self._get_redis_client()
            result = await redis_client.delete(session_id)

            logger.info(f"Deleted session: {session_id}")
            return result > 0

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False

    async def extend_session(self, session_id: str) -> bool:
        """
        Extend session TTL

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        try:
            redis_client = await self._get_redis_client()
            result = await redis_client.expire(session_id, self.session_ttl)

            if result:
                logger.debug(f"Extended session TTL: {session_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {str(e)}")
            return False

    async def get_active_sessions(self, user_id: str) -> List[str]:
        """
        Get all active sessions for a user

        Args:
            user_id: User identifier

        Returns:
            List of session IDs
        """
        try:
            redis_client = await self._get_redis_client()

            # Get all session keys
            session_keys = await redis_client.keys("session_*")

            active_sessions = []
            for session_key in session_keys:
                session_data = await redis_client.get(session_key)
                if session_data:
                    session_dict = json.loads(session_data)
                    if session_dict.get('user_id') == user_id:
                        active_sessions.append(session_key)

            logger.info(f"Found {len(active_sessions)} active sessions for user {user_id}")
            return active_sessions

        except Exception as e:
            logger.error(f"Failed to get active sessions: {str(e)}")
            return []

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis TTL should handle this automatically)

        Returns:
            Number of sessions cleaned up
        """
        try:
            redis_client = await self._get_redis_client()

            # Get all session keys
            session_keys = await redis_client.keys("session_*")

            cleaned_count = 0
            for session_key in session_keys:
                ttl = await redis_client.ttl(session_key)
                if ttl == -1:  # No TTL set
                    await redis_client.expire(session_key, self.session_ttl)
                elif ttl == -2:  # Key doesn't exist
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {str(e)}")
            return 0

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")