# services/ai_service.py
from openai import AsyncOpenAI, OpenAI
import json
from typing import List, Dict, Optional
from django.conf import settings
from apps.agents.models import Agent, KnowledgeDocument
from apps.conversations.models import Conversation, Message
import asyncio
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Initialize both sync and async clients
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def generate_response(
        self, 
        message: str, 
        agent: Agent, 
        conversation: Conversation,
        conversation_history: Optional[List[Dict]] = None,
        testing_agent: Optional[bool] = False
    ) -> str:
        """Generate AI response based on agent configuration and context"""
        
        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt(agent, conversation)
            
            # Get relevant knowledge
            # TODO
            knowledge_context = await self._get_relevant_knowledge(message, agent)
            
            # Build messages for OpenAI
            messages = self._build_message_history(
                system_prompt,
                knowledge_context,
                conversation_history or [],
                message
            )
            
            # Make API call to OpenAI
            response = await self._call_openai(
                messages=messages,
                model=agent.model,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            
            # Extract and clean the response
            ai_response = response.choices[0].message.content.strip()
            
            # Skip logging if testing agent at /agent/id/test
            if testing_agent == False:
                # Log token usage for billing
                await self._log_token_usage(
                    agent=agent,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens
                )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"AI Service Error: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    def _build_system_prompt(self, agent: Agent, conversation: Conversation) -> str:
        """Build comprehensive system prompt"""
        
        # Get customer info if available
        customer_info = ""
        if conversation.customer_name:
            customer_info = f"You are speaking with {conversation.customer_name}."
        
        prompt = f"""You are {agent.name}, an AI assistant for {agent.organization.name}.

{agent.system_prompt}

Personality and Behavior:
{agent.personality_traits}

{customer_info}

Important Guidelines:
- Be helpful, professional, and friendly
- Keep responses concise and clear
- If you don't know something, admit it honestly
- Never make up information
- Stay in character as described above
- Use the language: {agent.language}

Current conversation channel: {conversation.channel}
"""
        
        # Add business hours context if relevant
        if agent.business_hours:
            import datetime
            current_hour = datetime.datetime.now().hour
            # TODO: Check if within business hours
            
        return prompt
    
    async def _get_relevant_knowledge(self, query: str, agent: Agent) -> str:
        """Retrieve relevant knowledge from agent's knowledge base"""
        # TODO
        
        # Get all knowledge documents for the agent
        documents = await asyncio.to_thread(
            list,
            KnowledgeDocument.objects.filter(
                agent=agent, 
                is_processed=True
            ).values('title', 'content')[:5]  # Limit to top 5 for context window
        )
        
        if not documents:
            return ""
        
        # For now, concatenate all knowledge (later: implement vector search)
        knowledge_parts = []
        for doc in documents:
            knowledge_parts.append(f"[{doc['title']}]:\n{doc['content'][:1000]}")
        
        knowledge_context = "\n\n".join(knowledge_parts)
        
        return f"""
Relevant Information from Knowledge Base:
{knowledge_context}
"""
    
    def _build_message_history(
        self,
        system_prompt: str,
        knowledge_context: str,
        conversation_history: List[Dict],
        current_message: str
    ) -> List[Dict]:
        """Build the message array for OpenAI"""
        
        messages = []
        
        # System prompt with knowledge
        full_system_prompt = system_prompt
        if knowledge_context:
            full_system_prompt += f"\n\n{knowledge_context}"
        
        messages.append({"role": "system", "content": full_system_prompt})
        
        # Add conversation history (last 10 messages for context)
        for msg in conversation_history[-10:]:
            role = "user" if msg.get('sender_type') == 'customer' else "assistant"
            messages.append({"role": role, "content": msg.get('content', '')})
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    async def _call_openai(
        self,
        messages: List[Dict],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """Make async call to OpenAI API using new client"""
        
        try:
            # Use the async client for chat completions
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
            
        except Exception as e:
            # Check if it's a rate limit error and fallback to GPT-3.5
            if "rate_limit" in str(e).lower() or "429" in str(e):
                logger.warning("Rate limited on GPT-4, falling back to GPT-3.5-turbo")
                response = await self.async_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
            else:
                raise e
    
    async def _log_token_usage(
        self,
        agent: Agent,
        prompt_tokens: int,
        completion_tokens: int
    ):
        """Log token usage for billing purposes"""
        
        from apps.billing.models import UsageLog
        
        total_tokens = prompt_tokens + completion_tokens
        
        # Updated pricing as of 2024
        # GPT-4: $0.03/1K input tokens, $0.06/1K output tokens
        # GPT-3.5-turbo: $0.0005/1K input tokens, $0.0015/1K output tokens
        if agent.model == "gpt-4":
            cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        elif agent.model == "gpt-4-turbo-preview":
            cost = (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000
        else:  # gpt-3.5-turbo
            cost = (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000
        
        await asyncio.to_thread(
            UsageLog.objects.create,
            organization=agent.organization,
            agent=agent,
            usage_type='api_call',
            quantity=total_tokens,
            unit_cost=cost / total_tokens if total_tokens > 0 else 0,
            total_cost=cost
        )
    
    async def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (-1 to 1)"""
        
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Analyze the sentiment of the text and respond with only a number between -1 (very negative) and 1 (very positive)."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0,
                max_tokens=10
            )
            
            sentiment_str = response.choices[0].message.content.strip()
            return float(sentiment_str)
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return 0.0
    
    async def extract_intent(self, text: str, agent: Agent) -> Dict:
        """Extract intent and entities from message"""
        
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract the intent and any entities from the user message.
                        Respond in JSON format:
                        {
                            "intent": "primary intent",
                            "entities": {
                                "name": "...",
                                "email": "...",
                                "phone": "...",
                                "order_number": "..."
                            }
                        }"""
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0,
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
        except Exception as e:
            logger.error(f"Intent extraction error: {str(e)}")
            return {"intent": "general", "entities": {}}
    
    # Additional utility method for testing
    async def test_connection(self) -> bool:
        """Test if OpenAI API connection works"""
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'OK' if you receive this."}],
                max_tokens=10
            )
            return "OK" in response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False
        

class AIService_for_test_agent:
    ''' Purpose of this AI service is to provide a testing framework for desired AI agent customer created at /agent/id/test 
    - No logging usage
    - No conversation history/tracking
    - No token usage tracking
    -#! COMPLETELY SYNCRONOUS TO BE ABLE TO CALL IT IN THE API
    - Frontend sends conversation_history as an array of dicts with sender_type and content.
    '''

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_response(
        self, 
        message: str, 
        agent: Agent, 
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        """Generate AI response based on agent configuration and context"""
        
        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt(agent)
            
            # Get relevant knowledge
            # TODO
            knowledge_context = self._get_relevant_knowledge(message, agent)
            
            # Build messages for OpenAI
            messages = self._build_message_history(
                system_prompt,
                knowledge_context,
                conversation_history or [],
                message
            )
            
            # Make API call to OpenAI
            response = self._call_openai(
                messages=messages,
                model=agent.model,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            
            # Extract and clean the response
            ai_response = response.choices[0].message.content.strip()
            token_usage = response.usage.total_tokens

            return ai_response, token_usage
            
        except Exception as e:
            logger.error(f"AI Service Error: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    def _build_system_prompt(self, agent: Agent) -> str:
        """Build comprehensive system prompt"""        
        
        prompt = f"""You are {agent.name}, an AI assistant for {agent.organization.name}.

            {agent.system_prompt}

            Personality and Behavior:
            {agent.personality_traits}


            Important Guidelines:
            - Be helpful, professional, and friendly
            - Keep responses concise and clear
            - If you don't know something, admit it honestly
            - Never make up information
            - Stay in character as described above
            - Use the language: {agent.language}

            You are enabled to respond in the following channels:
            {', '.join(agent.get_enabled_channels())}
        """
        
        # Add business hours context if relevant
        if agent.business_hours:
            import datetime
            current_hour = datetime.datetime.now().hour
            # TODO: Check if within business hours
            
        return prompt
    
    def _get_relevant_knowledge(self, query: str, agent: Agent) -> str:
        """Retrieve relevant knowledge from agent's knowledge base"""
        
        # Get all knowledge documents for the agent
        documents = list(
            KnowledgeDocument.objects.filter(
                agent=agent,
                is_processed=True
            ).values('title', 'content')[:5]  # Limit to top 5 for context window
        )

        if not documents:
            return ""

        # For now, concatenate all knowledge (later: implement vector search)
        knowledge_parts = []
        for doc in documents:
            knowledge_parts.append(f"[{doc['title']}]:\n{doc['content'][:1000]}")
        knowledge_context = "\n\n".join(knowledge_parts)

        return f"""
                Relevant Information from Knowledge Base:
                {knowledge_context}
                """
    
    def _build_message_history(
        self,
        system_prompt: str,
        knowledge_context: str,
        conversation_history: List[Dict],
        current_message: str
    ) -> List[Dict]:
        """Build the message array for OpenAI"""
        
        messages = []
        
        # System prompt with knowledge
        full_system_prompt = system_prompt
        if knowledge_context:
            full_system_prompt += f"\n\n{knowledge_context}"
        
        messages.append({"role": "system", "content": full_system_prompt})
        
        # Add conversation history (last 10 messages for context)
        # conversation_history format = [{
        #     "sender_type": "customer",
        #     "content": "..."
        #  }, {
        #     "sender_type": "assistant",
        #     "content": "..."
        # }]
        for msg in conversation_history[-10:]:
            role = "user" if msg.get('sender_type') == 'customer' else "assistant"
            messages.append({"role": role, "content": msg.get('content', '')})
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _call_openai(
        self,
        messages: List[Dict],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """Make async call to OpenAI API using new client"""
        
        try:
            # Use the async client for chat completions
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
            
        except Exception as e:
            # Check if it's a rate limit error and fallback to GPT-3.5
            if "rate_limit" in str(e).lower() or "429" in str(e):
                logger.warning("Rate limited on GPT-4, falling back to GPT-3.5-turbo")
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
            else:
                raise e
            
    def extract_intent(self, text: str, agent: Agent) -> Dict:
        """Extract intent and entities from message"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract the intent and any entities from the user message.
                        Respond in JSON format:
                        {
                            "intent": "primary intent",
                            "entities": {
                                "name": "...",
                                "email": "...",
                                "phone": "...",
                                "order_number": "..."
                            }
                        }"""
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0,
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
        except Exception as e:
            logger.error(f"Intent extraction error: {str(e)}")
            return {"intent": "general", "entities": {}}