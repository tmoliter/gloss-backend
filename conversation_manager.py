"""
Simple Conversation Manager
Provides AI-powered conversations with custom prompts and validation tool calls
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
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
    is_valid: bool
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)

class ConversationResponse(BaseModel):
    message: str
    validation_result: Optional[ValidationResult] = None
    conversation_id: str
    processing_time_ms: float

class ConversationManager:
    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.active_conversations: Dict[str, ConversationState] = {}

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
        validation_result = await self._validate_response(conversation, user_message)
        
        # Add assistant response
        assistant_msg = Message(role="assistant", content=response_content)
        conversation.messages.append(assistant_msg)
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ConversationResponse(
            message=response_content,
            validation_result=validation_result,
            conversation_id=conversation_id,
            processing_time_ms=round(processing_time, 2)
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
        

    async def _validate_response(self, conversation: ConversationState, user_message: str) -> Optional[ValidationResult]:
        """Validate if user response matches the prompt expectation using OpenAI function calling"""
        unfulfilled_tools = [tool for tool in conversation.tools if tool.fulfilled == False]
        
        if not unfulfilled_tools:
            return None  # No validation needed if all tools are fulfilled

        # Create one validation function per unfulfilled tool
        validation_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,  # Each tool has its unique name
                "description": f"Validate if user response meets this condition: {tool.condition}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_valid": {
                            "type": "boolean",
                            "description": "True if the condition is met, False otherwise"
                        },
                        "reason": {
                            "type": "string", 
                            "description": "Brief explanation of why the response is valid or invalid"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the validation (0.0 to 1.0)"
                        }
                    },
                    "required": ["is_valid", "reason", "confidence"]
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
            
            # Process the tool calls
            if response.choices[0].message.tool_calls:
                # Take the first tool call result
                tool_call = response.choices[0].message.tool_calls[0]
                result = json.loads(tool_call.function.arguments)
                
                # Mark the specific tool as fulfilled if valid
                if result["is_valid"]:
                    for tool in conversation.tools:
                        if tool.name == tool_call.function.name:
                            tool.fulfilled = True
                            logger.info(f"✅ Tool '{tool.name}' marked as fulfilled")
                            break
                
                return ValidationResult(
                    is_valid=result["is_valid"],
                    reason=f"[{tool_call.function.name}] {result['reason']}",
                    confidence=result["confidence"]
                )
            
            return None  # No validation needed
            
        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return ValidationResult(
                is_valid=False,
                reason=f"Validation error: {str(e)}",
                confidence=0.0
            )

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