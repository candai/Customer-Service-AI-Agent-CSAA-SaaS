# services/elevenlabs_service.py
import asyncio
from django.conf import settings
import uuid
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import os
from django.utils import timezone

# New imports for the ElevenLabs SDK
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import ElevenLabs, Voice, VoiceSettings, Model

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
    
    # TODO: This needs to change in Production, saving locally now under /media/audio, not sustainable with large volume
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

class ElevenLabsServiceSynchronousForAgentVoicePreview:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        if self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("ElevenLabs API key not configured. ElevenLabsService will be disabled.")

    def get_available_voices(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get available voices - from cache if available and recent, otherwise from API
        
        Args:
            force_refresh: Force fetching from API even if cache exists
        """
        from apps.agents.models import ElevenLabsVoice
        
        # Check if we have cached voices that are less than 24 hours old
        if not force_refresh:
            cache_time_limit = timezone.now() - timedelta(hours=24)
            cached_voices = ElevenLabsVoice.objects.filter(
                is_active=True,
                updated_at__gte=cache_time_limit
            )
            
            if cached_voices.exists():
                logger.info("Returning cached ElevenLabs voices")
                return [self._voice_model_to_dict(voice) for voice in cached_voices]
        
        # Fetch from API
        if not self.client:
            return self._get_default_voices()
            
        try:
            voices_response = self.client.voices.get_all()
            voices = voices_response.voices
            
            # Update cache
            self._update_voice_cache(voices)
            
            return [self._voice_to_dict(voice) for voice in voices]
            
        except Exception as e:
            logger.error(f"ElevenLabs SDK Get voices error: {str(e)}")
            # Try to return from cache even if expired
            cached_voices = ElevenLabsVoice.objects.filter(is_active=True)
            if cached_voices.exists():
                logger.info("Returning expired cache due to API error")
                return [self._voice_model_to_dict(voice) for voice in cached_voices]
            return self._get_default_voices()

    def _update_voice_cache(self, voices: List[Voice]):
        """Update the database cache with fetched voices"""
        from apps.agents.models import ElevenLabsVoice
        
        try:
            # Mark all existing voices as inactive first
            ElevenLabsVoice.objects.update(is_active=False)
            
            # Update or create each voice
            for voice in voices:
                ElevenLabsVoice.objects.update_or_create(
                    voice_id=voice.voice_id,
                    defaults={
                        'name': voice.name,
                        'category': getattr(voice, 'category', ''),
                        'description': getattr(voice, 'description', ''),
                        'labels': getattr(voice, 'labels', {}),
                        'is_active': True,
                        'updated_at': timezone.now()
                    }
                )
            
            # Delete voices that haven't been seen in 30 days
            old_limit = timezone.now() - timedelta(days=30)
            ElevenLabsVoice.objects.filter(
                is_active=False,
                updated_at__lt=old_limit
            ).delete()
            
            logger.info(f"Updated cache with {len(voices)} voices")
            
        except Exception as e:
            logger.error(f"Failed to update voice cache: {e}")

    def generate_audio(self, text: str, voice_id: str, agent_id: Optional[str] = None) -> Optional[str]:
        """Generate audio synchronously for agent voice preview and return base64 encoded audio"""
        if not self.client:
            logger.error("ElevenLabs client not initialized. Check your API key.")
            return None
        
        try:
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_flash_v2_5",  # cheap & fast
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5
                )
            )
            
            # Concatenate the audio chunks into a single bytes object
            audio_content = b"".join(audio_stream)
            
            # Log usage for billing if agent_id provided
            if agent_id:
                self._log_usage(text, agent_id)
            
            # Return base64 encoded audio
            import base64
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            return audio_base64
            
        except Exception as e:
            logger.error(f"ElevenLabs SDK TTS error: {str(e)}")
            return None
    
    def _save_audio_file(self, audio_content: bytes, identifier: str) -> str:
        """Save audio file and return URL"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = uuid.uuid4().hex[:8]
        filename = f"audio_{identifier}_{timestamp}_{file_id}.mp3"
        
        media_dir = os.path.join(settings.MEDIA_ROOT, 'audio', 'previews')
        os.makedirs(media_dir, exist_ok=True)
        
        file_path = os.path.join(media_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(audio_content)
        
        audio_url = f"{settings.MEDIA_PUBLIC_DOMAIN}/media/audio/previews/{filename}"
        logger.info(f"Audio preview saved: {audio_url}")
        
        return audio_url
    
    def _log_usage(self, text: str, agent_id: str):
        """Log character usage for billing"""
        try:
            from apps.billing.models import UsageLog
            from apps.agents.models import Agent
            
            character_count = len(text)
            cost = (character_count / 1000) * 0.18  # $0.18 per 1000 chars
            
            agent = Agent.objects.get(id=agent_id)
            UsageLog.objects.create(
                organization=agent.organization,
                agent=agent,
                usage_type='tts_preview',
                quantity=character_count,
                unit_cost=0.00018,
                total_cost=cost
            )
            logger.info(f"Logged TTS preview usage: {character_count} characters")
            
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
    
    def _voice_to_dict(self, voice: Voice) -> Dict:
        """Convert Voice object to dictionary"""
        return {
            'voice_id': voice.voice_id,
            'name': voice.name,
            'category': getattr(voice, 'category', ''),
            'description': getattr(voice, 'description', ''),
            'labels': getattr(voice, 'labels', {})
        }
    
    def _voice_model_to_dict(self, voice_model) -> Dict:
        """Convert ElevenLabsVoice model to dictionary"""
        return {
            'voice_id': voice_model.voice_id,
            'name': voice_model.name,
            'category': voice_model.category,
            'description': voice_model.description,
            'labels': voice_model.labels
        }
    
    def _get_default_voices(self) -> List[Dict]:
        """Return default voices when API is unavailable"""
        return [
            {'voice_id': '21m00Tcm4TlvDq8ikWAM', 'name': 'Rachel', 'category': 'premade', 'description': 'Calm and composed'},
            {'voice_id': 'EXAVITQu4vr4xnSDxMaL', 'name': 'Sarah', 'category': 'premade', 'description': 'Soft and gentle'},
            {'voice_id': 'ErXwobaYiN019PkySvjV', 'name': 'Antoni', 'category': 'premade', 'description': 'Well-rounded'},
            {'voice_id': 'MF3mGyEYCl7XYWbV9V6O', 'name': 'Elli', 'category': 'premade', 'description': 'Young and energetic'},
            {'voice_id': 'TxGEqnHWrfWFTfGW9XjX', 'name': 'Josh', 'category': 'premade', 'description': 'Deep and resonant'},
        ]
