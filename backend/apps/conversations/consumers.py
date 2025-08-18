# apps/conversations/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from typing import Dict, Any, Optional
import json
import logging
import traceback


logger = logging.getLogger(__name__)

class BaseConsumer(AsyncJsonWebsocketConsumer):
    """Base consumer with common functionality"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Debug: Log what we have in scope
            # logger.info(f"BaseConsumer.connect() - Scope keys: {self.scope.keys()}")
            logger.info(f"User in scope: {self.scope.get('user')}")
            logger.info(f"User type: {type(self.scope.get('user'))}")
            
            # Get the user from scope
            user = self.scope.get("user")
            
            # Check if user exists and is authenticated
            if user is None:
                logger.error("User is None in scope")
                await self.close(code=4001)
                return
            
            # Check if it's AnonymousUser
            if isinstance(user, AnonymousUser):
                logger.error("User is AnonymousUser")
                await self.close(code=4001)
                return
            
            # Check if user has the required attributes
            if not hasattr(user, 'email'):
                logger.error(f"User object missing email attribute: {user}")
                await self.close(code=4001)
                return
            
            self.user = user
            logger.info(f"User authenticated: {self.user.email}")
            
            # Check organization
            if not hasattr(self.user, 'organization') or not self.user.organization:
                logger.error(f"User {self.user.email} has no organization")
                await self.close(code=4002)
                return
            
            self.organization_id = str(self.user.organization.id)
            logger.info(f"Organization ID: {self.organization_id}")
            
            # Set up groups
            await self.setup_groups()
            
            # Accept connection
            await self.accept()
            logger.info(f"WebSocket connection accepted for {self.user.email}")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}\n{traceback.format_exc()}")
            await self.close(code=4003)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            await self.cleanup_groups()
            if hasattr(self, 'user'):
                logger.info(f"WebSocket disconnected: User {self.user.email} (Code: {close_code})")
            else:
                logger.info(f"WebSocket disconnected (Code: {close_code})")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
    
    async def setup_groups(self):
        """Override in subclasses to set up channel groups"""
        pass
    
    async def cleanup_groups(self):
        """Override in subclasses to leave channel groups"""
        pass
    
    # async def send_initial_data(self):
    #     """Override in subclasses to send initial data"""
    #     pass
    
    async def receive_json(self, content):
        """Handle incoming WebSocket messages"""
        try:
            message_type = content.get('type')
            handler = getattr(self, f'handle_{message_type}', None)
            
            if handler:
                await handler(content)
            else:
                await self.send_error(f"Unknown message type: {message_type}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}\n{traceback.format_exc()}")
            try:
                await self.send_error(f"Error processing message: {str(e)}")
                logger.error(f"Error sending error message: {str(e)}")
            except:
                logger.error("Failed to send error message to client")
                pass  # Even if we can't send error, don't crash
    
    async def handle_ping(self, content):
        """Handle ping messages from client"""
        if content.get('type') == 'ping':
            logger.info("Received ping from client")
            await self.send_json({'type': 'pong'})
        else:
            logger.warning(f"Received unknown ping type: {content.get('type')}")
            pass  # Ignore unknown ping types
        

    
    async def send_error(self, message: str):
        """Send error message to client"""
        try:
            await self.send_json({
                'type': 'error',
                'message': message
            })
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
            # Don't crash if we can't send error, just log it


class ConversationConsumer(BaseConsumer):
    """Consumer for conversation-related real-time updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("ConversationConsumer initialized")

    # TODO: Group_add function is not implemented 
    async def setup_groups(self):
        """Join organization and user groups"""
        try:
            # Organization group - for all conversations in the org
            self.org_group = f'org_{self.organization_id}'
            await self.channel_layer.group_add(self.org_group, self.channel_name)
            # logger.info(f"Added to org group: {self.org_group}")

        
            # User group - for user-specific updates
            self.user_group = f'user_{self.user.id}'
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            # logger.info(f"Added to user group: {self.user_group}")
        except Exception as e:
            logger.error(f"Error in setup_groups: {str(e)}", exc_info=True)
            raise e

    
    async def cleanup_groups(self):
        """Leave all groups"""
        try:
            if hasattr(self, 'org_group'):
                await self.channel_layer.group_discard(self.org_group, self.channel_name)
            if hasattr(self, 'user_group'):
                await self.channel_layer.group_discard(self.user_group, self.channel_name)
        except Exception as e:
            logger.error(f"Error in cleanup_groups: {str(e)}")


    async def handle_get_conversations(self, content):
        """Handle request to get conversations list"""
        conversations = await self.get_active_conversations()
        await self.send_json({
            'type': 'conversations_list',
            'conversations': conversations
        })
        logger.info(f"Sent {len(conversations)} conversations on request")

    
    @database_sync_to_async
    def get_active_conversations(self):
        """Get active conversations for organization"""
        from apps.conversations.models import Conversation
        try:
            conversations = Conversation.objects.filter(
                agent__organization_id=self.organization_id,
                status__in=['active', 'waiting']
            ).select_related('agent').order_by('-last_message_at')[:50]
            
            result = []
            for conv in conversations:
                try:
                    result.append({
                        'id': str(conv.id),
                        'agent_id': str(conv.agent.id),
                        'agent_name': conv.agent.name,
                        'customer_phone': conv.customer_phone,
                        'customer_name': conv.customer_name or 'Unknown',
                        'channel': conv.channel,
                        'status': conv.status,
                        'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
                        'message_count': conv.message_count,
                        'unread_count': 0  # TODO: Implement unread count
                        }
                    )
                except Exception as conv_error:
                    logger.error(f"Error processing conversation {conv.id}: {str(conv_error)}")
            return result

        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    # Handlers for incoming messages
    async def handle_get_conversation(self, content):
        """Handle request for specific conversation"""
        try:
            conversation_id = content.get('conversation_id')
            if not conversation_id:
                await self.send_error("Conversation ID required")
                return
            
            conversation_data = await self.get_conversation_detail(conversation_id)
            if conversation_data:
                await self.send_json({
                    'type': 'conversation_detail',
                    'conversation': conversation_data
                })
            else:
                await self.send_error("Conversation not found")
    
        except Exception as e:
            logger.error(f"Error getting conversation detail: {str(e)}", exc_info=True)
            await self.send_error(f"Error getting conversation: {str(e)}")

    @database_sync_to_async
    def get_conversation_detail(self, conversation_id):
        """Get detailed conversation with messages"""
        from apps.conversations.models import Conversation, Message
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                agent__organization_id=self.organization_id
            )
            
            messages = Message.objects.filter(
                conversation=conversation
            ).order_by('created_at')[:100]
            
            return {
                'id': str(conversation.id),
                'agent_id': str(conversation.agent.id),
                'agent_name': conversation.agent.name,
                'customer_phone': conversation.customer_phone,
                'customer_name': conversation.customer_name,
                'channel': conversation.channel,
                'status': conversation.status,
                'started_at': conversation.started_at.isoformat(),
                'messages': [
                    {
                        'id': str(msg.id),
                        'sender_type': msg.sender_type,
                        'content': msg.content,
                        'message_type': msg.message_type,
                        'created_at': msg.created_at.isoformat(),
                        'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None
                    }
                    for msg in messages
                ]
            }
        except Conversation.DoesNotExist:
            return None
    
    async def handle_send_message(self, content):
        """Handle sending a message (human agent takeover)"""
        conversation_id = content.get('conversation_id')
        message_text = content.get('message')
        
        if not conversation_id or not message_text:
            await self.send_error("Conversation ID and message required")
            return
        
        # Send message through the system
        success = await self.send_human_message(conversation_id, message_text)
        
        if success:
            await self.send_json({
                'type': 'message_sent',
                'conversation_id': conversation_id
            })
        else:
            await self.send_error("Failed to send message")
    
    @database_sync_to_async
    def send_human_message(self, conversation_id, message_text):
        """Send a message as human agent"""
        from apps.conversations.models import Conversation, Message
        from services.message_processor import MessageProcessor
        import asyncio
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                agent__organization_id=self.organization_id
            )
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender_type='human',
                content=message_text,
                message_type='text'
            )
            
            # Mark conversation as handed off if not already
            if conversation.status != 'handed_off':
                conversation.status = 'handed_off'
                conversation.assigned_to = self.user
                conversation.handed_off_at = timezone.now()
                conversation.save()
            
            # Based on the message channel, process the message
            channel = conversation.channel

            #! Send message through the appropriate channel
            processor = MessageProcessor()
            asyncio.run(processor._send_response(
                channel = channel,
                phone_number=conversation.customer_phone,
                to_number=conversation.customer_phone,
                agent= conversation.agent,
                response=message_text,
            ))
            logger.info(f"Message sent successfully: {message_text} to {conversation.customer_phone}")
            
            
            return True
        except Exception as e:
            logger.error(f"Send message error: {str(e)}")
            return False
    
    async def handle_end_conversation(self, content):
        """Handle ending a conversation"""
        conversation_id = content.get('conversation_id')
        
        if not conversation_id:
            await self.send_error("Conversation ID required")
            return
        
        success = await self.end_conversation(conversation_id)
        
        if success:
            await self.send_json({
                'type': 'conversation_ended',
                'conversation_id': conversation_id
            })
    
    @database_sync_to_async
    def end_conversation(self, conversation_id):
        """End a conversation"""
        from apps.conversations.models import Conversation
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                agent__organization_id=self.organization_id
            )
            
            conversation.status = 'ended'
            conversation.ended_at = timezone.now()
            conversation.save()
            
            return True
        except Exception as e:
            logger.error(f"End conversation error: {str(e)}")
            return False
    
    # Handlers for events from channel layer
    async def conversation_update(self, event):
        """Handle conversation update from channel layer"""
        try:
            logger.info(f"📨 Received conversation_update event")
            # logger.info(f"   Event keys: {event.keys()}")
            logger.info(f"   Conversation ID: {event.get('conversation_id')}")

            # Send to WebSocket client
            try:
                # testing minimal message structure
                minimal_response = {
                    'type': 'conversation_update',
                    'conversation_id': str(event.get('conversation_id', 'unknown'))
                }
                
                # Try to send minimal first
                try:
                    await self.send_json(minimal_response)
                    logger.info(f"✅ Sent minimal update to client")
                except Exception as send_error:
                    logger.error(f"Error sending minimal update: {send_error}")
                    return


                # send full data if available
                conversation_id = event.get('conversation_id', 'unknown')
                update_type = event.get('update_type', 'message')
                data = event.get('data', {})
                
                logger.info(f"   Processing update for conversation: {conversation_id}")

                # Send to the WebSocket client
                message_to_send = {
                    'type': 'conversation_update',
                    'conversation_id': conversation_id,
                    'update_type': update_type,
                    'data': data
                }
                logger.info(f"   Sending to WebSocket client...")

                await self.send_json(message_to_send)
                logger.info(f"✅ Successfully sent update to client")
                
            except Exception as send_error:
                logger.error(f"Error sending to WebSocket: {str(send_error)}", exc_info=True)

        except Exception as e:
            logger.error(f"Error sending conversation update: {str(e)}", exc_info=True)

    
    async def new_conversation(self, event):
        """Handle new conversation event"""
        await self.send_json({
            'type': 'new_conversation',
            'conversation': event['conversation']
        })
    
    async def conversation_status_changed(self, event):
        """Handle conversation status change"""
        await self.send_json({
            'type': 'conversation_status_changed',
            'conversation_id': event['conversation_id'],
            'old_status': event['old_status'],
            'new_status': event['new_status']
        })


class AgentConsumer(BaseConsumer):
    """Consumer for agent-specific updates"""
    
    async def setup_groups(self):
        """Join agent-specific group"""
        self.agent_id = self.scope['url_route']['kwargs']['agent_id']
        
        # Verify user has access to this agent
        if not await self.verify_agent_access():
            await self.close(code=4003)
            return
        
        self.agent_group = f'agent_{self.agent_id}'
        await self.channel_layer.group_add(self.agent_group, self.channel_name)
    
    @database_sync_to_async
    def verify_agent_access(self):
        """Verify user has access to the agent"""
        from apps.agents.models import Agent
        
        try:
            Agent.objects.get(
                id=self.agent_id,
                organization_id=self.organization_id
            )
            return True
        except Agent.DoesNotExist:
            return False
    
    async def cleanup_groups(self):
        """Leave agent group"""
        if hasattr(self, 'agent_group'):
            await self.channel_layer.group_discard(self.agent_group, self.channel_name)
    
    @database_sync_to_async
    def get_agent_data(self):
        """Get agent data with stats"""
        from apps.agents.models import Agent
        from apps.conversations.models import Conversation
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        agent = Agent.objects.get(id=self.agent_id)
        
        # Get conversation stats
        now = datetime.now()
        today = now.date()
        
        stats = Conversation.objects.filter(
            agent=agent
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            today=Count('id', filter=Q(started_at__date=today))
        )
        
        return {
            'id': str(agent.id),
            'name': agent.name,
            'is_active': agent.is_active,
            'channels': {
                'whatsapp': agent.whatsapp_enabled,
                'sms': agent.sms_enabled,
                'voice': agent.voice_enabled
            },
            'stats': stats
        }
    
    # Event handlers from channel layer
    async def agent_status_changed(self, event):
        """Handle agent status change"""
        await self.send_json({
            'type': 'agent_status_changed',
            'agent_id': event['agent_id'],
            'is_active': event['is_active']
        })
    
    async def agent_stats_update(self, event):
        """Handle agent stats update"""
        await self.send_json({
            'type': 'agent_stats_update',
            'stats': event['stats']
        })


class OrganizationConsumer(BaseConsumer):
    """Consumer for organization-wide updates"""
    
    async def setup_groups(self):
        """Join organization admin group"""
        # Only allow admin/owner users
        if self.user.role not in ['admin', 'owner']:
            await self.close(code=4002)
            return
        
        self.org_admin_group = f'org_admin_{self.organization_id}'
        await self.channel_layer.group_add(self.org_admin_group, self.channel_name)
    
    async def cleanup_groups(self):
        """Leave organization admin group"""
        if hasattr(self, 'org_admin_group'):
            await self.channel_layer.group_discard(self.org_admin_group, self.channel_name)
    
    @database_sync_to_async
    def get_organization_data(self):
        """Get organization data with usage"""
        from apps.accounts.models import Organization
        from apps.billing.models import UsageLog
        from django.db.models import Sum
        from datetime import datetime
        from django.db.models import Q
        
        org = Organization.objects.get(id=self.organization_id)
        
        # Get current month usage
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        usage = UsageLog.objects.filter(
            organization=org,
            created_at__gte=month_start
        ).aggregate(
            total_messages=Sum('quantity', filter=Q(usage_type='message')),
            total_minutes=Sum('quantity', filter=Q(usage_type='voice_minute')),
            total_cost=Sum('total_cost')
        )
        
        return {
            'id': str(org.id),
            'name': org.name,
            'subscription_tier': org.subscription_tier,
            'usage': {
                'messages': usage['total_messages'] or 0,
                'voice_minutes': usage['total_minutes'] or 0,
                'cost': float(usage['total_cost'] or 0),
                'message_limit': org.monthly_message_limit,
                'voice_limit': org.monthly_voice_minutes_limit
            }
        }
    
    # Event handlers
    async def usage_update(self, event):
        """Handle usage update"""
        await self.send_json({
            'type': 'usage_update',
            'usage': event['usage']
        })
    
    async def team_member_joined(self, event):
        """Handle new team member"""
        await self.send_json({
            'type': 'team_member_joined',
            'member': event['member']
        })