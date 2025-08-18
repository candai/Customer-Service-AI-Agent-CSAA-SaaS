# services/elevenlabs_service.py
import asyncio
from django.conf import settings
import uuid
from typing import Optional
import logging
from datetime import datetime
import os

# New imports for the ElevenLabs SDK
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import Voice, VoiceSettings, Model

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        # Initialize the async client once
        if self.api_key:
            self.client = AsyncElevenLabs(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("ElevenLabs API key not configured. ElevenLabsService will be disabled.")
        
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel)
        agent_id: str = None,
        stability: float = 0.5,
        similarity_boost: float = 0.5
    ) -> Optional[str]:
        """Convert text to speech using the ElevenLabs SDK and return audio URL"""
        
        if not self.client:
            logger.error("ElevenLabs client not initialized. Check your API key.")
            return None
        
        try:
            # Use the SDK to generate the audio stream
            # The SDK returns an async iterator of audio chunks
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_flash_v2_5", # cheap & fast
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity_boost
                )
            )
            
            # Concatenate the audio chunks into a single bytes object
            audio_content = b"".join([chunk async for chunk in audio_stream])
            
            # Your internal logic for saving the file remains the same
            audio_url = await self._save_audio_file(
                audio_content, 
                agent_id
            )
            logger.info(f"ElevenLabs TTS: Audio file saved: {audio_url}")
            
            # Your internal logic for logging usage remains the same
            await self._log_usage(text, agent_id)
            logger.info("Logged Voice usage for billing")
            
            return audio_url
                    
        except Exception as e:
            # The SDK will raise its own specific errors, e.g., elevenlabs.APIError
            logger.error(f"ElevenLabs SDK TTS error: {str(e)}")
            return None
    
    # This internal method does not need to change
    async def _save_audio_file(self, audio_content: bytes, agent_id: str) -> str:
        """Save audio file and return URL"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = uuid.uuid4().hex[:8]
        filename = f"audio_{agent_id}_{timestamp}_{file_id}.mp3"
        
        media_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(media_dir, exist_ok=True)
        
        file_path = os.path.join(media_dir, filename)
        
        # We need to run this synchronous file write in a separate thread
        # to avoid blocking the async event loop.
        await asyncio.to_thread(self._write_file_sync, file_path, audio_content)

        logger.info(f"Audio file saved to {settings.MEDIA_PUBLIC_DOMAIN}/media/audio/{filename}")
        
        return f"{settings.MEDIA_PUBLIC_DOMAIN}/media/audio/{filename}"

    def _write_file_sync(self, file_path: str, audio_content: bytes):
        """Synchronous helper to write file content."""
        with open(file_path, 'wb') as f:
            f.write(audio_content)
    
    # This internal method does not need to change
    async def _log_usage(self, text: str, agent_id: str):
        from asgiref.sync import sync_to_async
        """Log character usage for billing"""
        
        def db_operations():
            from apps.billing.models import UsageLog
            from apps.agents.models import Agent

            character_count = len(text)
            cost = (character_count / 1000) * 0.18
            
            if agent_id:
                try:
                    agent = Agent.objects.get(id=agent_id)
                    UsageLog.objects.create(
                        organization=agent.organization,
                        agent=agent,
                        usage_type='tts_characters',
                        quantity=character_count,
                        unit_cost=0.00018,
                        total_cost=cost
                    )
                except Agent.DoesNotExist:
                    logger.error(f"Agent with id {agent_id} not found for usage logging.")
                except Exception as e:
                    logger.error(f"Error during usage logging db operations: {e}")

        try:
            await sync_to_async(db_operations, thread_sensitive=True)()
        except Exception as e:
            logger.error(f"Usage logging error: {str(e)}")
    
    async def get_voices(self) -> list[Voice]:
        """Get list of available voices using the ElevenLabs SDK"""
        
        if not self.client:
            return []
            
        try:
            # Use the SDK to get all voices
            voices_response = await self.client.voices.get_all()
            return voices_response.voices
        except Exception as e:
            logger.error(f"SDK Get voices error: {str(e)}")
            return []