# apps/webhooks/api.py
from datetime import datetime
from ninja import Router
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from services.message_processor import MessageProcessor
from services.twilio_service import TwilioService
from services.elevenlabs_service import ElevenLabsService
from apps.agents.models import Agent
import asyncio
import logging
from django.conf import settings

router = Router(tags=["Webhooks"])
logger = logging.getLogger(__name__)

@router.post("/twilio/whatsapp", auth=None)
@csrf_exempt
async def whatsapp_webhook(request):
    """Handle incoming WhatsApp messages from Twilio"""
    
    try:
        # Validate webhook is from Twilio
        twilio_service = TwilioService()
        #! Validates that webhook is from Twilio", for local dev using ngrok must comment out this line
        # if not twilio_service.validate_webhook(request):
        #     logger.warning("Invalid Twilio webhook signature")
        #     return HttpResponse(status=403)
        
        # Parse Twilio webhook data
        data = request.POST
        from_number = data.get('From', '').replace('whatsapp:', '')
        to_number = data.get('To', '').replace('whatsapp:', '')
        message_body = data.get('Body', '')
        message_sid = data.get('MessageSid', '')
        media_url = data.get('MediaUrl0')  # First media attachment if any
        
        logger.info(f"WhatsApp message from {from_number}: {message_body[:50]}")
        
        # Process message asynchronously
        # CRITICAL CHANGE: Use create_task to process in background
        # This returns immediately without waiting
        asyncio.create_task(
            process_whatsapp_message_async(
                from_number=from_number,
                to_number=to_number,
                message_body=message_body,
                media_url=media_url,
                message_sid=message_sid
            )
        )
        
        # Return empty response to Twilio
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}", exc_info=True)
        return HttpResponse(status=500)
    
async def process_whatsapp_message_async(
    from_number: str,
    to_number: str,
    message_body: str,
    media_url: str,
    message_sid: str
):
    """Process WhatsApp message in background - doesn't block webhook"""
    try:
        processor = MessageProcessor()
        result = await processor.process_incoming_message(
            channel='whatsapp',
            from_number=from_number,
            to_number=to_number,
            message_content=message_body,
            media_url=media_url,
            external_id=message_sid
        )
        
        logger.info(f"WhatsApp message processed in background: {result.get('success')}")
        
    except Exception as e:
        logger.error(f"Background processing error: {str(e)}", exc_info=True)


@router.post("/twilio/sms", auth=None)
@csrf_exempt
async def sms_webhook(request):
    """Handle incoming SMS messages from Twilio"""
    
    try:
        # Validate webhook
        twilio_service = TwilioService()
        if not twilio_service.validate_webhook(request):
            return HttpResponse(status=403)
        
        data = request.POST
        from_number = data.get('From', '')
        to_number = data.get('To', '')
        message_body = data.get('Body', '')
        message_sid = data.get('MessageSid', '')
        
        logger.info(f"SMS from {from_number}: {message_body[:50]}")
        
        # Process in background
        asyncio.create_task(
            process_sms_message_async(
                from_number=from_number,
                to_number=to_number,
                message_body=message_body,
                message_sid=message_sid
            )
        )
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"SMS webhook error: {str(e)}", exc_info=True)
        return HttpResponse(status=500)
    
async def process_sms_message_async(
    from_number: str,
    to_number: str,
    message_body: str,
    message_sid: str
):
    """Process SMS in background"""
    try:
        processor = MessageProcessor()
        result = await processor.process_incoming_message(
            channel='sms',
            from_number=from_number,
            to_number=to_number,
            message_content=message_body,
            external_id=message_sid
        )
        
        logger.info(f"SMS processed in background: {result.get('success')}")
        
    except Exception as e:
        logger.error(f"SMS background processing error: {str(e)}", exc_info=True)


@router.post("/twilio/voice", auth=None)
@csrf_exempt
async def voice_incoming_webhook(request):
    """Handle incoming voice calls"""
    
    try:
        data = request.POST
        from_number = data.get('From', '')
        to_number = data.get('To', '')
        call_sid = data.get('CallSid', '')
        
        logger.info(f"Incoming call from {from_number} to {to_number}")
        
        # Find agent by voice number
        try:
            # Find agent quickly
            agent = await asyncio.to_thread(
                lambda: Agent.objects.select_related('organization').get(
                    voice_number=to_number,
                    voice_enabled=True,
                    is_active=True
                )
            )
            logger.info(f"Found agent {agent.name} for call {call_sid}")
        except Agent.DoesNotExist:
            twilio_service = TwilioService()
            twiml = twilio_service.generate_twiml_response(
                text="Sorry, this number is not currently in service.",
                gather_input=False
            )
            logger.warning(f"No active agent found for number {to_number}")
            return HttpResponse(twiml, content_type='text/xml')
        
        # Generate TwiML quickly
        # Generate initial greeting
        twilio_service = TwilioService()
        
        # If agent has custom welcome message, use it
        greeting = agent.welcome_message or "Hello! How can I help you today?"
        
        # Generate TwiML with greeting and gather
        # INSTEAD USING ELEVENLABS SDK FOR SERVING WELCOME MESSAGES
        # action_url = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/twilio/voice/process/{agent.id}"
        # twiml = twilio_service.generate_twiml_response(
        #     text=greeting,
        #     gather_input=True,
        #     action_url=action_url,
        #     language=agent.language or 'en-US'
        # )
        
        # Generate audio URL using ElevenLabs
        elevenlabs_service = ElevenLabsService()
        audio_url = await elevenlabs_service.text_to_speech(
            text=greeting,
            voice_id=agent.voice_id,
            agent_id=str(agent.id)
        )
        logger.info(f"Generated audio URL: {audio_url}")            
        
        # Build TwiML response
        action_url = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/twilio/voice/process/{agent.id}"
        
        if audio_url:
            # Use ElevenLabs audio
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Gather input="speech" action="{action_url}" method="POST" speechTimeout="auto" language="{agent.language or 'en-US'}"/>
</Response>'''
        else:
            # Fallback to Twilio TTS if ElevenLabs fails
            logger.warning("ElevenLabs failed, falling back to Twilio TTS")
            twilio_service = TwilioService()
            twiml = twilio_service.generate_twiml_response(
                text=greeting,
                gather_input=True,
                action_url=action_url,
                language=agent.language or 'en-US'
            )

        
        # Create conversation in background
        asyncio.create_task(
            create_voice_conversation_async(agent, from_number)
        )
        
        return HttpResponse(twiml, content_type='text/xml')
        
    except Exception as e:
        logger.error(f"Voice webhook error: {str(e)}", exc_info=True)
        # Return error TwiML
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>We're experiencing technical difficulties. Please try again later.</Say>
            <Hangup/>
        </Response>"""
        return HttpResponse(twiml, content_type='text/xml')
    
async def create_voice_conversation_async(agent, from_number):
    """Create voice conversation in background"""
    try:
        processor = MessageProcessor()
        await processor._get_or_create_conversation(
            agent=agent,
            channel='voice',
            customer_phone=from_number
        )
    except Exception as e:
        logger.error(f"Voice conversation creation error: {str(e)}")


@router.post("/twilio/voice/process/{agent_id}", auth=None)
@csrf_exempt
async def voice_process_webhook(request, agent_id: str):
    """Process speech input from voice call"""
    
    try:
        data = request.POST
        speech_result = data.get('SpeechResult', '')
        from_number = data.get('From', '')
        call_sid = data.get('CallSid', '')
        
        logger.info(f"Speech input: {speech_result[:50]}")
        
        if not speech_result:
            # No speech detected, ask to repeat
            twilio_service = TwilioService()
            action_url = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/twilio/voice/process/{agent_id}"
            twiml = twilio_service.generate_twiml_response(
                text="I didn't catch that. Could you please repeat?",
                gather_input=True,
                action_url=action_url
            )
            return HttpResponse(twiml, content_type='text/xml')
        
        # Process the speech
        processor = MessageProcessor()
        result = await processor.process_voice_speech(
            speech_text=speech_result,
            agent_id=agent_id,
            from_number=from_number,
            call_sid=call_sid
        )
        
        # Generate TwiML response
        twilio_service = TwilioService()
        
        if result.get('success') and result.get('send_result', {}).get('audio_url'):
            # Play the AI-generated audio response
            action_url = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/twilio/voice/process/{agent_id}"
            twiml = twilio_service.generate_play_twiml(
                audio_url=result['send_result']['audio_url'],
                gather_speech=True,
                action_url=action_url
            )
        else:
            # Fallback to text-to-speech
            response_text = result.get('response', "I'm having trouble processing your request.")
            action_url = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/twilio/voice/process/{agent_id}"
            twiml = twilio_service.generate_twiml_response(
                text=response_text,
                gather_input=True,
                action_url=action_url
            )
        
        return HttpResponse(twiml, content_type='text/xml')
        
    except Exception as e:
        logger.error(f"Voice process error: {str(e)}", exc_info=True)
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>I'm having technical difficulties. Please try again.</Say>
            <Hangup/>
        </Response>"""
        return HttpResponse(twiml, content_type='text/xml')

@router.post("/twilio/status", auth=None)
@csrf_exempt
async def status_webhook(request):
    """Handle Twilio status callbacks"""
    
    try:
        data = request.POST
        message_sid = data.get('MessageSid')
        message_status = data.get('MessageStatus')
        
        if message_sid and message_status:
            # Update status in background
            asyncio.create_task(
                update_message_status_async(
                    message_sid,
                    message_status,
                    data.get('ErrorMessage')
                )
            )
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Status webhook error: {str(e)}")
        return HttpResponse(status=200)  # Always return 200 to prevent retries
    

async def update_message_status_async(message_sid: str, status: str, error_message: str = None):
    """Update message status in background"""
    try:
        from apps.conversations.models import Message
        
        message = await asyncio.to_thread(
            Message.objects.get,
            external_id=message_sid
        )
        
        if status == 'delivered':
            message.delivered_at = datetime.now()
        elif status == 'read':
            message.read_at = datetime.now()
        elif status == 'failed':
            message.is_error = True
            message.error_message = error_message or 'Delivery failed'
        
        await asyncio.to_thread(message.save)
        
    except Message.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Status update error: {str(e)}")