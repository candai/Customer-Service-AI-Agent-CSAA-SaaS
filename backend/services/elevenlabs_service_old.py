# services/elevenlabs_service.py
import aiohttp
import asyncio
from django.conf import settings
import uuid
from typing import Optional, Dict
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.api_url = "https://api.elevenlabs.io/v1"
        
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel)
        agent_id: str = None,
        stability: float = 0.5,
        similarity_boost: float = 0.5
    ) -> Optional[str]:
        """Convert text to speech and return audio URL"""
        
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return None
        
        url = f"{self.api_url}/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": "eleven_flash_v2_5",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        audio_content = await response.read()
                        
                        # Save audio file locally or to S3
                        audio_url = await self._save_audio_file(
                            audio_content, 
                            agent_id
                        )
                        logger.info(f"ElevenLabs TTS: Audio file saved: {audio_url}")
                        
                        # Log usage for billing
                        await self._log_usage(text, agent_id)
                        logger.info("Logged Voice usage for billing")
                        
                        return audio_url
                    else:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {str(e)}")
            return None
    
    async def _save_audio_file(self, audio_content: bytes, agent_id: str) -> str:
        """Save audio file and return URL"""
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = uuid.uuid4().hex[:8]
        filename = f"audio_{agent_id}_{timestamp}_{file_id}.mp3"
        
        # For now, save locally. In production, upload to S3
        media_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(media_dir, exist_ok=True)
        
        file_path = os.path.join(media_dir, filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(audio_content)
        
        # Return URL
        return f"{settings.BACKEND_URL}/media/audio/{filename}"
    
    async def _log_usage(self, text: str, agent_id: str):
        from asgiref.sync import sync_to_async
        """Log character usage for billing"""
        
        # try:
        #     from apps.billing.models import UsageLog
        #     from apps.agents.models import Agent
            
        #     character_count = len(text)
        #     # ElevenLabs pricing: ~$0.18 per 1000 characters
        #     cost = (character_count / 1000) * 0.18
            
        #     if agent_id:
        #         agent = await asyncio.to_thread(
        #             Agent.objects.get,
        #             id=agent_id
        #         )
                
        #         await asyncio.to_thread(
        #             UsageLog.objects.create,
        #             organization=agent.organization,
        #             agent=agent,
        #             usage_type='voice_minute',  # Approximation
        #             quantity=character_count / 150,  # ~150 chars per minute of speech
        #             unit_cost=cost / (character_count / 150) if character_count > 0 else 0,
        #             total_cost=cost
        #         )
        # except Exception as e:
        #     logger.error(f"Usage logging error: {str(e)}")
        def db_operations():
            from apps.billing.models import UsageLog
            from apps.agents.models import Agent

            character_count = len(text)
            # ElevenLabs pricing: ~$0.18 per 1000 characters
            cost = (character_count / 1000) * 0.18
            
            if agent_id:
                try:
                    # All ORM calls happen inside this sync function
                    agent = Agent.objects.get(id=agent_id)
                    
                    UsageLog.objects.create(
                        organization=agent.organization,
                        agent=agent,
                        usage_type='tts_characters', # More accurate type
                        quantity=character_count,
                        unit_cost=0.00018, # Cost per character
                        total_cost=cost
                    )
                except Agent.DoesNotExist:
                    logger.error(f"Agent with id {agent_id} not found for usage logging.")
                except Exception as e:
                    # Catch potential db errors inside the thread
                    logger.error(f"Error during usage logging db operations: {e}")

        try:
            # Now, call our synchronous function from the async context
            # using the sync_to_async adapter.
            # thread_sensitive=True is crucial for Django ORM operations.
            await sync_to_async(db_operations, thread_sensitive=True)()

        except Exception as e:
            # This will catch errors related to the async execution itself.
            logger.error(f"Usage logging error: {str(e)}")
    
    async def get_voices(self) -> list:
        """Get list of available voices"""
        
        url = f"{self.api_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('voices', [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"Get voices error: {str(e)}")
            return []
    