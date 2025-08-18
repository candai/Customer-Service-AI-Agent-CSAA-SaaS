# services/twilio_service.py
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator
from django.conf import settings
from typing import Optional, Dict
import logging
import asyncio

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        self.webhook_base_url = settings.WEBHOOK_BASE_URL
        
    # WhatsApp Methods
    async def send_whatsapp_message(
        self, 
        to_number: str, 
        from_number: str, 
        message: str,
        media_url: Optional[str] = None
    ) -> Dict:
        """Send WhatsApp message via Twilio"""
        
        try:
            # Format numbers for WhatsApp
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            if not from_number.startswith('whatsapp:'):
                from_number = f'whatsapp:{from_number}'
            
            msg_params = {
                'from_': from_number,
                'to': to_number,
                'body': message
            }
            
            if media_url:
                msg_params['media_url'] = [media_url]
            
            # Send message asynchronously
            message_instance = await asyncio.to_thread(
                self.client.messages.create,
                **msg_params
            )
            
            return {
                'success': True,
                'sid': message_instance.sid,
                'status': message_instance.status,
                'to': message_instance.to,
                'from': message_instance.from_
            }
            
        except Exception as e:
            logger.error(f"WhatsApp send error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # SMS Methods
    async def send_sms(
        self, 
        to_number: str, 
        from_number: str, 
        message: str
    ) -> Dict:
        """Send SMS via Twilio"""
        
        try:
            # Truncate message if too long
            if len(message) > 1600:
                message = message[:1597] + '...'
            
            msg_instance = await asyncio.to_thread(
                self.client.messages.create,
                from_=from_number,
                to=to_number,
                body=message
            )
            
            # Log usage for billing
            from apps.billing.models import UsageLog
            from apps.agents.models import Agent
            
            try:
                agent = await asyncio.to_thread(
                    Agent.objects.get,
                    sms_number=from_number
                )
                
                await asyncio.to_thread(
                    UsageLog.objects.create,
                    organization=agent.organization,
                    agent=agent,
                    usage_type='message',
                    quantity=1,
                    unit_cost=0.0075,  # Typical SMS cost
                    total_cost=0.0075
                )
            except Agent.DoesNotExist:
                logger.warning(f"No agent found for SMS number {from_number}, skipping usage log.")
                pass
            
            return {
                'success': True,
                'sid': msg_instance.sid,
                'status': msg_instance.status
            }
            
        except Exception as e:
            logger.error(f"SMS send error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Voice Methods
    def generate_twiml_response(
        self,
        text: str = None,
        voice: str = "alice",
        language: str = "en-US",
        gather_input: bool = False,
        action_url: str = None
    ) -> str:
        """Generate TwiML response for voice calls"""
        
        response = VoiceResponse()
        
        if gather_input and action_url:
            gather = Gather(
                input='speech',
                action=action_url,
                method='POST',
                speech_timeout='auto',
                language=language
            )
            if text:
                gather.say(text, voice=voice, language=language)
            response.append(gather)
        elif text:
            response.say(text, voice=voice, language=language)
        
        return str(response)
    
    def generate_play_twiml(self, audio_url: str, gather_speech: bool = True, action_url: str = None) -> str:
        """Generate TwiML to play audio file"""
        
        response = VoiceResponse()
        
        # Play the audio
        response.play(audio_url)
        
        # Continue gathering speech if needed
        if gather_speech and action_url:
            gather = Gather(
                input='speech',
                action=action_url,
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            response.append(gather)
        
        return str(response)
    
    async def make_call(
        self,
        to_number: str,
        from_number: str,
        twiml_url: str
    ) -> Dict:
        """Initiate an outbound call"""
        
        try:
            call = await asyncio.to_thread(
                self.client.calls.create,
                to=to_number,
                from_=from_number,
                url=twiml_url,
                method='POST'
            )
            
            return {
                'success': True,
                'sid': call.sid,
                'status': call.status
            }
            
        except Exception as e:
            logger.error(f"Call initiation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_webhook(self, request) -> bool:
        """Validate that webhook is from Twilio"""
        
        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
        url = request.build_absolute_uri()
        
        # Get POST parameters
        post_vars = {}
        for key, value in request.POST.items():
            post_vars[key] = value
        
        return self.validator.validate(url, post_vars, signature)
    
    # Phone Number Management
    async def provision_phone_number(
        self,
        area_code: str = None,
        capabilities: Dict = None
    ) -> Optional[str]:
        """Search for and provision a phone number"""
        
        if capabilities is None:
            capabilities = {
                'sms_enabled': True,
                'mms_enabled': True,
                'voice_enabled': True
            }
        
        try:
            # Search for available numbers
            available = await asyncio.to_thread(
                self.client.available_phone_numbers('US').local.list,
                area_code=area_code,
                limit=1,
                **capabilities
            )
            
            if not available:
                return None
            
            # Purchase the number
            phone_number = available[0].phone_number
            
            purchased = await asyncio.to_thread(
                self.client.incoming_phone_numbers.create,
                phone_number=phone_number,
                sms_url=f"{self.webhook_base_url}/api/webhooks/sms",
                sms_method='POST',
                voice_url=f"{self.webhook_base_url}/api/webhooks/voice",
                voice_method='POST'
            )
            
            return purchased.phone_number
            
        except Exception as e:
            logger.error(f"Phone provisioning error: {str(e)}")
            return None
    
    async def release_phone_number(self, phone_number: str) -> bool:
        """Release a phone number back to Twilio"""
        
        try:
            # Find the number
            numbers = await asyncio.to_thread(
                self.client.incoming_phone_numbers.list,
                phone_number=phone_number,
                limit=1
            )
            
            if numbers:
                await asyncio.to_thread(
                    numbers[0].delete
                )
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Phone release error: {str(e)}")
            return False
    
    async def setup_whatsapp_sandbox(self, webhook_url: str) -> Dict:
        """Setup WhatsApp sandbox for testing"""
        
        # Note: This is typically done manually in Twilio Console
        # This method just returns the sandbox number and instructions
        
        return {
            'sandbox_number': settings.TWILIO_WHATSAPP_NUMBER,
            'join_code': 'join <your-sandbox-keyword>',
            'webhook_url': f"{webhook_url}/api/webhooks/whatsapp",
            'instructions': 'Send "join <your-sandbox-keyword>" to the sandbox number to start testing'
        }