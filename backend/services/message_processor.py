# services/message_processor.py
from typing import Dict, Any, Optional
from apps.agents.models import Agent
from apps.conversations.models import Conversation, Message
from .ai_service import AIService
from .twilio_service import TwilioService
from .elevenlabs_service import ElevenLabsService
import asyncio
from channels.layers import get_channel_layer
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class MessageProcessor:
    def __init__(self):
        self.ai_service = AIService()
        self.twilio_service = TwilioService()
        self.elevenlabs_service = ElevenLabsService()
        self.channel_layer = get_channel_layer()
    
    async def process_incoming_message(
        self,
        channel: str,  # 'whatsapp', 'sms', 'voice'
        from_number: str,
        to_number: str,
        message_content: str,
        media_url: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process incoming message from any channel"""
        
        try:
            logger.info(f"📥 Processing {channel} message from {from_number}")

            # Clean phone numbers
            from_number = from_number.replace('whatsapp:', '').replace('sms:', '')
            to_number = to_number.replace('whatsapp:', '').replace('sms:', '')
            
            # Find agent by phone number
            agent = await self._find_agent_by_number(channel, to_number)
            if not agent:
                logger.error(f"No agent found for {channel} number: {to_number}")
                return {'error': 'Agent not found'}
            
            # Check if agent is active
            if not agent.is_active:
                return {'error': 'Agent is not active'}
            
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                agent, channel, from_number
            )
            
            # Store incoming message
            incoming_message = await self._store_message(
                conversation=conversation,
                sender_type='customer',
                content=message_content,
                message_type='image' if media_url else 'text',
                media_url=media_url,
                external_id=external_id
            )
            
            # Get conversation history
            history = await self._get_conversation_history(conversation)
            
            # Generate AI response
            ai_response = await self.ai_service.generate_response(
                message=message_content,
                agent=agent,
                conversation=conversation,
                conversation_history=history
            )
            
            # Apply typing delay for realism
            if agent.response_delay_seconds > 0 and channel != 'voice':
                await asyncio.sleep(agent.response_delay_seconds)
            
            # Send response based on channel
            send_result = await self._send_response(
                channel=channel,
                to_number=from_number,
                agent=agent,
                response=ai_response
            )
            
            # Store AI response
            ai_message = await self._store_message(
                conversation=conversation,
                sender_type='agent',
                content=ai_response,
                message_type='text',
                external_id=send_result.get('sid') if send_result.get('success') else None,
                delivered_at=timezone.now() if send_result.get('success') else None
            )
            
            # Update conversation metrics
            await self._update_conversation_metrics(conversation, incoming_message, ai_message)
            
            # Analyze sentiment
            sentiment = await self.ai_service.analyze_sentiment(message_content)
            conversation.sentiment_score = sentiment
            await asyncio.to_thread(conversation.save)

            await asyncio.sleep(0.1) # Small delay to ensure WebSocket connection is stable
            
            # Broadcast update via WebSocket
            logger.info(f"🔍 Conversation details before broadcast:")
            logger.info(f"   Conversation ID: {conversation.id}")
            logger.info(f"   Agent ID: {conversation.agent.id}")
            logger.info(f"   Agent Org ID: {conversation.agent.organization_id}")
            try:
                logger.info(f"📢 About to broadcast update for conversation {conversation.id}")
                await self._broadcast_conversation_update(conversation)
                logger.info(f"✅ Broadcast completed successfully")
            except Exception as e:
                logger.error(f"❌ Broadcast failed: {str(e)}", exc_info=True)


            
            return {
                'success': True,
                'conversation_id': str(conversation.id),
                'message_id': str(ai_message.id),
                'response': ai_response,
                'send_result': send_result
            }
           
        except Exception as e:
            logger.error(f"Message processing error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _find_agent_by_number(self, channel: str, number: str) -> Optional[Agent]:
        """Find agent by phone number based on channel"""
    
        try:
            if channel == 'whatsapp':
                agent = await asyncio.to_thread(
                    lambda: Agent.objects.select_related('organization').get(
                        whatsapp_number=number,
                        whatsapp_enabled=True,
                        is_active=True  # Added is_active check
                    )
                )
            elif channel == 'sms':
                agent = await asyncio.to_thread(
                    lambda: Agent.objects.select_related('organization').get(
                        sms_number=number,
                        sms_enabled=True,
                        is_active=True  # Added is_active check
                    )
                )
            elif channel == 'voice':
                agent = await asyncio.to_thread(
                    lambda: Agent.objects.select_related('organization').get(
                        voice_number=number,
                        voice_enabled=True,
                        is_active=True  # This was already here
                    )
                )
            else:
                return None
                
            return agent
            
        except Agent.DoesNotExist:
            logger.warning(f"Message_processor: No active agent found for {channel} number: {number}")
            return None
    
    async def _get_or_create_conversation(
        self, 
        agent: Agent, 
        channel: str, 
        customer_phone: str
    ) -> Conversation:
        """Get existing or create new conversation"""
        
        # Look for active conversation
        try:
            conversation = await asyncio.to_thread(
                Conversation.objects.get,
                agent=agent,
                channel=channel,
                customer_phone=customer_phone,
                status='active'
            )
        except Conversation.DoesNotExist:
            # Create new conversation
            conversation = await asyncio.to_thread(
                Conversation.objects.create,
                agent=agent,
                channel=channel,
                customer_phone=customer_phone,
                status='active'
            )
            
            # Send welcome message if it's a new conversation
            if agent.welcome_message:
                await self._send_welcome_message(agent, channel, customer_phone)
        
        return conversation
    
    async def _send_welcome_message(
        self,
        agent: Agent,
        channel: str,
        customer_phone: str
    ):
        """Send welcome message for new conversations"""
        
        try:
            if channel == 'whatsapp':
                await self.twilio_service.send_whatsapp_message(
                    to_number=customer_phone,
                    from_number=agent.whatsapp_number,
                    message=agent.welcome_message
                )
            elif channel == 'sms':
                await self.twilio_service.send_sms(
                    to_number=customer_phone,
                    from_number=agent.sms_number,
                    message=agent.welcome_message
                )
        except Exception as e:
            logger.error(f"Welcome message error: {str(e)}")
    
    async def _store_message(
        self,
        conversation: Conversation,
        sender_type: str,
        content: str,
        message_type: str = 'text',
        media_url: Optional[str] = None,
        external_id: Optional[str] = None,
        delivered_at: Optional[timezone.datetime] = None
    ) -> Message:
        """Store message in database"""
        
        message = await asyncio.to_thread(
            Message.objects.create,
            conversation=conversation,
            sender_type=sender_type,
            content=content,
            message_type=message_type,
            media_url=media_url or '',
            external_id=external_id or '',
            delivered_at=delivered_at
        )
        
        return message
    
    async def _get_conversation_history(
        self,
        conversation: Conversation,
        limit: int = 20
    ) -> list:
        """Get recent conversation history"""
        
        messages = await asyncio.to_thread(
            lambda: list(
                Message.objects.filter(conversation=conversation)
                .order_by('-created_at')[:limit]
                .values('sender_type', 'content', 'created_at')
            )
        )
        
        # Reverse to get chronological order
        messages.reverse()
        
        return messages
    
    async def _send_response(
        self,
        channel: str,
        to_number: str,
        agent: Agent,
        response: str
    ) -> Dict:
        """Send response through appropriate channel"""
        
        if channel == 'whatsapp':
            return await self.twilio_service.send_whatsapp_message(
                to_number=to_number,
                from_number=agent.whatsapp_number,
                message=response
            )
        elif channel == 'sms':
            return await self.twilio_service.send_sms(
                to_number=to_number,
                from_number=agent.sms_number,
                message=response
            )
        elif channel == 'voice':
            # For voice, convert to speech first
            audio_url = await self.elevenlabs_service.text_to_speech(
                text=response,
                voice_id=agent.voice_id or "21m00Tcm4TlvDq8ikWAM",
                agent_id=str(agent.id)
            )
            print(f"Message Processor: Audio URL: {audio_url}")
            return {
                'success': True if audio_url else False,
                'audio_url': audio_url
            }
        
        return {'success': False, 'error': 'Unknown channel'}
    
    async def _update_conversation_metrics(
        self,
        conversation: Conversation,
        incoming_message: Message,
        outgoing_message: Message
    ):
        """Update conversation metrics"""
        
        # Update conversation fields
        conversation.message_count += 2
        conversation.customer_message_count += 1
        conversation.agent_message_count += 1
        conversation.last_message_at = timezone.now()
        
        # Calculate response time for first response
        if conversation.customer_message_count == 1:
            delta = outgoing_message.created_at - incoming_message.created_at
            conversation.first_response_time_seconds = int(delta.total_seconds())
        
        # Save conversation in thread to avoid blocking
        await asyncio.to_thread(conversation.save)
        
        # Update agent metrics
        # Django needs to perform a synchronous database query to fetch the related Agent object. Since the _update_conversation_metrics function is async, this synchronous call blocks the event loop, which is forbidden in an asynchronous context. Converting to 
        #agent = conversation.agent
        # Use asyncio.to_thread to safely access the related agent
        
        # Get agent in thread to avoid blocking
        agent = await asyncio.to_thread(lambda: conversation.agent)
        agent.total_messages += 2
        await asyncio.to_thread(agent.save, update_fields=['total_messages'])
    

    async def _broadcast_conversation_update(self, conversation: Conversation):
        """Send real-time update to dashboard via WebSocket"""
        
        logger.info(f"📡 _broadcast_conversation_update called for conversation {conversation.id}")

        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()

            if not channel_layer:
                logger.error("Channel layer not configured")
                return
            
            logger.info(f"✅ Channel layer obtained: {type(channel_layer)}")

            # Ensure organization_id is valid
            org_id = str(conversation.agent.organization_id)
            group_name = f"org_{org_id}"
            logger.info(f"🔔 Broadcasting to group: {group_name}")


            # Now try with more data
            try:
                # Get latest messages - but handle errors
                recent_messages = []
                try:
                    messages = await asyncio.to_thread(
                        lambda: list(
                            Message.objects.filter(conversation=conversation)
                            .order_by('-created_at')[:5]
                            .values('id', 'sender_type', 'content', 'created_at', 'message_type')
                        )
                    )
                    
                    # Format messages safely
                    for msg in messages:
                        try:
                            formatted_msg = {
                                'id': str(msg['id']),
                                'sender_type': msg['sender_type'],
                                'content': str(msg['content'])[:500],  # Limit content length
                                'message_type': msg['message_type']
                            }
                            
                            # Check if created_at is already a string or datetime
                            if msg['created_at']:
                                if hasattr(msg['created_at'], 'isoformat'):
                                    formatted_msg['created_at'] = msg['created_at'].isoformat()
                                else:
                                    formatted_msg['created_at'] = str(msg['created_at'])
                            
                            recent_messages.append(formatted_msg)
                        except Exception as msg_error:
                            logger.error(f"Error formatting message: {msg_error}")
                            
                except Exception as e:
                    logger.error(f"Error fetching messages: {str(e)}")
                
                # Prepare full broadcast data with safe defaults
                full_broadcast_data = {
                    "type": "conversation_update",
                    "conversation_id": str(conversation.id),
                    "update_type": "new_message",
                    "data": {
                        "messages": recent_messages,
                        "status": getattr(conversation, 'status', 'active'),
                        "channel": getattr(conversation, 'channel', 'whatsapp'),
                        "customer_phone": getattr(conversation, 'customer_phone', 'unknown')
                    }
                }
                
                # Add last_message_at safely
                if hasattr(conversation, 'last_message_at') and conversation.last_message_at:
                    try:
                        if hasattr(conversation.last_message_at, 'isoformat'):
                            full_broadcast_data['data']['last_message_at'] = conversation.last_message_at.isoformat()
                        else:
                            full_broadcast_data['data']['last_message_at'] = str(conversation.last_message_at)
                    except:
                        pass
                
                logger.info(f"📤 Sending full broadcast")
                await channel_layer.group_send(group_name, full_broadcast_data)
                logger.info(f"✅ Full broadcast sent")
                
            except Exception as e:
                logger.error(f"Error sending full broadcast: {str(e)}", exc_info=True)
                
        except Exception as e:
            logger.error(f"❌ WebSocket broadcast error: {str(e)}", exc_info=True)
    

    async def _broadcast_new_conversation(self, conversation: Conversation):
        """Broadcast new conversation event"""
        
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            conversation_data = {
                'id': str(conversation.id),
                'agent_id': str(conversation.agent.id),
                'agent_name': conversation.agent.name,
                'customer_phone': conversation.customer_phone,
                'channel': conversation.channel,
                'status': conversation.status,
                'started_at': conversation.started_at.isoformat()
            }
            
            # Broadcast to organization
            await channel_layer.group_send(
                f"org_{conversation.agent.organization_id}",
                {
                    "type": "new_conversation",
                    "conversation": conversation_data
                }
            )
            
        except Exception as e:
            logger.error(f"New conversation broadcast error: {str(e)}")


    async def process_voice_speech(
        self,
        speech_text: str,
        agent_id: str,
        from_number: str,
        call_sid: str
    ) -> Dict:
        """Process speech input from voice call"""
        
        try:
            # Get agent
            agent = await asyncio.to_thread(
                Agent.objects.select_related('organization').get,
                id=agent_id
            )
            
            # Process as voice message
            result = await self.process_incoming_message(
                channel='voice',
                from_number=from_number,
                to_number=agent.voice_number,
                message_content=speech_text,
                external_id=call_sid
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Voice processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
    
    async def end_conversation(
        self,
        conversation_id: str,
        reason: str = 'completed'
    ):
        """End a conversation"""
        
        try:
            conversation = await asyncio.to_thread(
                Conversation.objects.get,
                id=conversation_id
            )
            
            conversation.status = 'ended'
            conversation.ended_at = timezone.now()
            
            # Calculate total duration
            if conversation.started_at:
                delta = conversation.ended_at - conversation.started_at
                conversation.resolution_time_seconds = int(delta.total_seconds())
            
            await asyncio.to_thread(conversation.save)
            
            # Update agent metrics
            #agent = conversation.agent
            # Use asyncio.to_thread to safely access the related agent
            agent = await asyncio.to_thread(lambda: conversation.agent)
            agent.total_conversations += 1
            await asyncio.to_thread(agent.save, update_fields=['total_conversations'])
            
            # Send final message if configured
            if reason == 'timeout':
                timeout_message = "This conversation has been ended due to inactivity. Feel free to message again if you need further assistance."
                await self._send_response(
                    channel=conversation.channel,
                    to_number=conversation.customer_phone,
                    agent=agent,
                    response=timeout_message
                )
            
            # Broadcast update
            await self._broadcast_conversation_update(conversation)
            
        except Exception as e:
            logger.error(f"End conversation error: {str(e)}")

    # Synchronous method to send human message
    # frontend: conv/id human message
    def send_human_message_sync(self, conversation_id: str, message_text: str) -> bool:
        """Synchronous method to send human message"""
        from apps.conversations.models import Conversation
        
        try:
            conversation = Conversation.objects.select_related('agent').get(id=conversation_id)
            
            # Create a new event loop for this sync call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the async method in the new loop
                result = loop.run_until_complete(
                    self._send_response(
                        channel= conversation.channel,
                        to_number= conversation.customer_phone,
                        agent=conversation.agent,
                        response=message_text
                    )
                )
                return True
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error sending human message: {e}")
            return False