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

logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationState(BaseModel):
    conversation_id: str
    user_id: str
    language: str = "es"
    custom_prompt: str = ""
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
        language: str = "es", 
        custom_prompt: str = "I am an old man who will ask you how old you are"
    ) -> str:
        """Start a new conversation session with custom prompt"""
        conversation_id = str(uuid.uuid4())
        
        # Create system message with language constraint and custom prompt
        system_message = f"""You are roleplaying based on this prompt: "{custom_prompt}"
        
        IMPORTANT: You must ONLY respond in {language}. Do not use any other language.
        Stay in character and follow the roleplay scenario described in the prompt.
        Keep responses natural and conversational."""
        
        conversation = ConversationState(
            conversation_id=conversation_id,
            user_id=user_id,
            language=language,
            custom_prompt=custom_prompt,
            messages=[Message(role="system", content=system_message)]
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
        """Generate natural conversation response using function calling for better roleplay"""
        
        # Define roleplay response tool
        response_tool = {
            "type": "function", 
            "function": {
                "name": "generate_roleplay_response",
                "description": "Generate an appropriate response for the roleplay scenario",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": f"Response in {conversation.language} that fits the roleplay scenario"
                        },
                        "stays_in_character": {
                            "type": "boolean", 
                            "description": "Whether the response stays true to the roleplay prompt"
                        }
                    },
                    "required": ["response", "stays_in_character"]
                }
            }
        }
        
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=[response_tool],
                tool_choice={"type": "function", "function": {"name": "generate_roleplay_response"}},
                max_tokens=150,
                temperature=0.7
            )
            
            # Extract the function call result
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                if tool_call.function.name == "generate_roleplay_response":
                    import json
                    result = json.loads(tool_call.function.arguments)
                    return result["response"]
            
            # Fallback to regular response
            return response.choices[0].message.content or "Lo siento, no entendí."
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Lo siento, tuve un problema técnico."

    async def _validate_response(self, conversation: ConversationState, user_message: str) -> Optional[ValidationResult]:
        """Validate if user response matches the prompt expectation using OpenAI function calling"""
        
        # Define the validation tool
        validation_tool = {
            "type": "function",
            "function": {
                "name": "validate_user_response",
                "description": "Validate if the user's response appropriately addresses what was asked in the roleplay prompt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_valid": {
                            "type": "boolean",
                            "description": "True if the user appropriately responded to the prompt, False otherwise"
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
        }
        
        validation_prompt = f"""
        Roleplay context: "{conversation.custom_prompt}"
        User's response: "{user_message}"
        
        Analyze if the user's response appropriately addresses what was expected based on the roleplay prompt.
        Consider context, relevance, and whether they're engaging with the scenario as intended.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": validation_prompt}],
                tools=[validation_tool],
                tool_choice={"type": "function", "function": {"name": "validate_user_response"}},
                max_tokens=150,
                temperature=0.1
            )
            
            # Extract the function call result
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                if tool_call.function.name == "validate_user_response":
                    import json
                    result = json.loads(tool_call.function.arguments)
                    
                    return ValidationResult(
                        is_valid=result["is_valid"],
                        reason=result["reason"],
                        confidence=result["confidence"]
                    )
            
            # Fallback if no tool call
            return ValidationResult(
                is_valid=False,
                reason="Unable to validate response",
                confidence=0.0
            )
            
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