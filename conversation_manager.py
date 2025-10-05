"""
Simple Conversation Manager
Provides AI-powered conversations with custom prompts and validation tool calls
"""

from typing import Dict, List, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from nlp import MorphemeResponse, NaturalLanguageProcessor
from openai import AsyncOpenAI
import uuid
from datetime import datetime, timedelta
import logging
import asyncio
import json

from prompting.utils import get_prompt
from prompting.prompts import ToolCall, get_character_prompt
from utils import language_map


logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationState(BaseModel):
    conversation_id: str
    user_id: str
    language: str
    character_info: str
    conversation_instructions: str
    journal_words: List[str] = []
    tools: List[ToolCall] = []
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    total_messages: int = 0

class ValidationResult(BaseModel):
    name: str
    is_valid: bool
    reason: str

class ConversationResponse(BaseModel):
    message: str
    validation_results: List[ValidationResult]
    conversation_id: str
    processing_time_ms: float
    morphemes: MorphemeResponse

class ConversationManager:
    def __init__(self, openai_api_key: str, nlp: NaturalLanguageProcessor):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.active_conversations: Dict[str, ConversationState] = {}
        self.nlp = nlp

    async def start_conversation(
        self, 
        user_id: str, 
        language: str, 
        name: str,
        journal_words: List[str] = []
    ) -> str:
        """Start a new conversation session with custom prompt"""
        conversation_id = str(uuid.uuid4())

        # Get character prompt components
        prompt_components = get_character_prompt(name)
        system_message = get_prompt(
            language=language, 
            character_info=prompt_components.character_info, 
            conversation_instructions=prompt_components.conversation_instructions, 
            journal_words=journal_words
        )

        conversation = ConversationState(
            conversation_id=conversation_id,
            user_id=user_id,
            language=language,
            messages=[Message(role="system", content=system_message)],
            character_info=prompt_components.character_info,
            conversation_instructions=prompt_components.conversation_instructions,
            journal_words=journal_words,
            tools=prompt_components.tools
        )
        
        self.active_conversations[conversation_id] = conversation
        logger.info(f"🎯 Started conversation in {language} for user {user_id}")
        
        return conversation_id

    async def send_message_stream(self, conversation_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """Send a message and stream AI response using Server-Sent Events"""
        if conversation_id not in self.active_conversations:
            yield f"data: {json.dumps({'error': f'Conversation {conversation_id} not found'})}\n\n"
            return
        
        conversation = self.active_conversations[conversation_id]
        
        # Add user message
        user_msg = Message(role="user", content=user_message)
        conversation.messages.append(user_msg)
        conversation.total_messages += 1
        conversation.last_activity = datetime.now()
        
        # Stream AI response
        full_response = ""
        async for chunk in self._generate_stream_response(conversation):
            if chunk:
                full_response += chunk
                # Send SSE formatted data
                yield f"data: {json.dumps({'chunk': chunk, 'type': 'content'})}\n\n"
        
        # Add complete response to conversation history
        assistant_msg = Message(role="assistant", content=full_response)
        conversation.messages.append(assistant_msg)
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'complete', 'conversation_id': conversation_id})}\n\n"

    async def _generate_stream_response(self, conversation: ConversationState) -> AsyncGenerator[str, None]:
        """Generate streaming response from OpenAI"""
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages
        ]
        
        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Sorry, I couldn't generate a response: {str(e)}"

    async def send_message(self, conversation_id: str, user_message: str) -> ConversationResponse:
        """Send a message and get AI response with optional validation"""
        start_time = asyncio.get_event_loop().time()
        
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.active_conversations[conversation_id]
        
        # Add user message
        user_msg = Message(role="user", content=user_message)
        conversation.messages.append(user_msg)
        conversation.total_messages += 1
        conversation.last_activity = datetime.now()
        
        # Generate AI response
        response_content = await self._generate_response(conversation)
        
        # Optional: Validate if user answered the prompt correctly
        validation_results = await self._validate_response(conversation, user_message)
        
        # Add assistant response
        assistant_msg = Message(role="assistant", content=response_content)
        conversation.messages.append(assistant_msg)

        try:
            morphemes = self.nlp.get_morphemes(response_content, conversation.language)
        except Exception as e:
            logger.error(f"Error getting morphemes: {e}")
            raise e

        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ConversationResponse(
            message=response_content,
            validation_results=validation_results,
            conversation_id=conversation_id,
            processing_time_ms=round(processing_time, 2),
            morphemes=morphemes
        )

    async def _generate_response(self, conversation: ConversationState) -> str:
        """Generate response - simple and fast"""
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content or "No response generated"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I couldn't generate a response."
        

    async def _validate_response(self, conversation: ConversationState, user_message: str) -> List[ValidationResult]:
        """Validate if user response matches the prompt expectation using OpenAI function calling"""
        unfulfilled_tools = [tool for tool in conversation.tools if tool.fulfilled == False]
        
        if not unfulfilled_tools:
            return []  # No validation needed if all tools are fulfilled

        # Create one validation function per unfulfilled tool
        validation_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,  # Each tool has its unique name
                "description": f"Validate if user response meets this condition: {tool.condition}",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_valid": {
                            "type": "boolean",
                            "description": "True if the condition is met, False otherwise"
                        },
                        "reason": {
                            "type": "string", 
                            "description": "Brief explanation of why the response is valid or invalid   ."
                        },
                    },
                    "required": ["is_valid", "reason"],
                    "additionalProperties": False,
                }
            }
        } for tool in unfulfilled_tools]
        
        validation_prompt = f"""Evaluate the user's response against these conditions:

    Conditions to check:
    {chr(10).join([f"- {tool.name}: {tool.condition}" for tool in unfulfilled_tools])}

    User's response: "{user_message}"
    Target language: "{language_map[conversation.language]}"

    Call the appropriate validation function(s) for any conditions that the user's response addresses.
    The response must be entirely in understandable {language_map[conversation.language]}."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": validation_prompt}],
                tools=validation_tools,
                # No tool_choice - let OpenAI decide which tools to call
                max_tokens=150,
                temperature=0.1
            )
            validation_results: List[ValidationResult] = []
            # Process the tool calls
            if response.choices[0].message.tool_calls:
                # Take the first tool call result
                for tool_call in response.choices[0].message.tool_calls:
                    result = json.loads(tool_call.function.arguments)
                    tool_call_name = tool_call.function.name
                    
                    # Mark the specific tool as fulfilled if valid
                    if result["is_valid"]:
                        for tool in conversation.tools:
                            if tool.name == tool_call_name:
                                tool.fulfilled = True
                                logger.info(f"Tool '{tool.name}' marked as fulfilled")
                                break

                    validation_results.append(
                        ValidationResult(
                            name=tool_call_name,
                            is_valid=result["is_valid"],
                            reason=f"[{tool_call_name}] {result['reason']}",
                        )
                    )

            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return []

    def get_conversation_history(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation history"""
        return self.active_conversations.get(conversation_id)

    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up conversations older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [
            conv_id for conv_id, conv in self.active_conversations.items()
            if conv.last_activity < cutoff_time
        ]
        
        for conv_id in to_remove:
            del self.active_conversations[conv_id]
        
        logger.info(f"🧹 Cleaned up {len(to_remove)} old conversations")