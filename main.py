from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
from typing import List, Dict, Optional
import logging
import asyncio
import os
from contextlib import asynccontextmanager
import time
from dotenv import load_dotenv
from nlp import MorphemeResponse, NaturalLanguageProcessor

# Load environment variables from .env file
load_dotenv()

# Import conversation manager
from conversation_manager import (
    ConversationManager, 
    ConversationResponse,
    ConversationState
)

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger(__name__)

# Globals
conversation_manager: Optional[ConversationManager] = None
nlp: Optional[NaturalLanguageProcessor] = None


async def preload_priority_models():
    """Preload Spanish and Japanese models at startup for game performance"""
    logger.info("🚀 Preloading priority language models for game...")
    
    for lang, model_name in nlp.PRIORITY_LANGUAGES.items():
        logger.info(f"Loading model for language: {lang}")
        try:
            start_time = time.time()
            nlp.models[lang] = spacy.load(model_name)
            load_time = time.time() - start_time
            logger.info(f"✅ Loaded {model_name} in {load_time:.2f}s")
        except OSError:
            logger.warning(f"⚠️ {model_name} not found - install with: python -m spacy download {model_name}")
            nlp.models[lang] = None
    
    # Warm up models with test text for even faster first requests
    if nlp.models.get("es"):
        nlp.models["es"]("Hola mundo")
        logger.info("🔥 Spanish model warmed up")

    if nlp.models.get("ja"):
        nlp.models["ja"]("こんにちは")
        logger.info("🔥 Japanese model warmed up")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global conversation_manager
    global nlp
    nlp = NaturalLanguageProcessor()

    # Initialize conversation manager if OpenAI API key is available
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        conversation_manager = ConversationManager(openai_api_key, nlp)
        logger.info("🤖 Conversation manager initialized")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not found - conversation features disabled")
    
    await preload_priority_models()
    logger.info("🎮 Gloss NLP Backend ready for game!")
    yield
    # Shutdown
    if conversation_manager:
        conversation_manager.cleanup_old_conversations()
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title="Gloss NLP Backend - Game Optimized",
    description="High-performance NLP backend optimized for language learning games",
    version="2.1.0",
    lifespan=lifespan
)

# Configure CORS - optimized for game deployment
def get_cors_origins():
    """Get CORS origins from environment or use defaults"""
    env_origins = os.environ.get("ALLOWED_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",")]
    
    # Default origins for development
    return [
        "http://localhost:3000",        # Next.js dev
        "http://localhost:3001",        # Alternative Next.js dev port
        "https://gloss-brown.vercel.app",  # Your specific Vercel deployment
        "https://*.vercel.app",         # Vercel deployments (backup)
        "https://vercel.app",           # Vercel domain
        "https://*.up.railway.app",     # Railway deployments
        "https://up.railway.app",       # Railway domain
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Added OPTIONS for preflight
    allow_headers=["*"],
)

# Request/Response models optimized for language learning game
class TokenizeRequest(BaseModel):
    text: str
    language: str = "es"  # Default to Spanish for game
    include_morphology: bool = True  # Important for language learning
    include_pos: bool = True
    include_lemma: bool = True
    include_dependencies: bool = False  # Optional for advanced features

class TokenInfo(BaseModel):
    text: str
    lemma: Optional[str] = None
    pos: Optional[str] = None
    tag: Optional[str] = None
    morphology: Optional[Dict[str, str]] = None
    dep: Optional[str] = None  # Dependency relation (optional)
    head_text: Optional[str] = None  # Head token (optional)
    is_alpha: bool
    is_digit: bool
    is_punct: bool
    is_space: bool

class TokenizeResponse(BaseModel):
    tokens: List[TokenInfo]
    sentences: List[str]
    language: str
    word_count: int
    processing_time_ms: float  # Performance tracking for game

class MorphemeRequest(BaseModel):
    text: str
    language: str = "es"  # Default to Spanish
    include_features: bool = True  # Morphological features are key for language learning


# Conversation API Models
class StartConversationRequest(BaseModel):
    user_id: str
    language: str
    name: str
    journal_words: List[str] = []

class StartConversationResponse(BaseModel):
    conversation_id: str
    message: str = "Starting conversation..."
    language: str

class SendMessageRequest(BaseModel):
    conversation_id: str
    message: str

class ConversationHistoryResponse(BaseModel):
    conversation: Optional[ConversationState]
    total_messages: int
    language: str
    character_info: str
    conversation_instructions: str
    journal_words: List[str] = []

@app.get("/")
async def root():
    """Health check endpoint for game backend"""
    conversation_status = "enabled" if conversation_manager else "disabled"
    nlp = NaturalLanguageProcessor()
    return {
        "message": "🎮 Gloss NLP Backend - Game Ready",
        "version": "2.1.0",
        "priority_languages": list(nlp.PRIORITY_LANGUAGES.keys()),
        "all_supported": list(nlp.SUPPORTED_LANGUAGES.keys()),
        "preloaded_models": [lang for lang, model in nlp.models.items() if model is not None],
        "features": ["morphology", "lemmatization", "conversations", "game_optimized"],
        "conversation_ai": conversation_status
    }

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    return {
        "status": "healthy",
        "preloaded_models": [lang for lang, model in nlp.models.items() if model is not None],
        "supported_languages": list(nlp.SUPPORTED_LANGUAGES.keys()),
        "priority_languages": list(nlp.PRIORITY_LANGUAGES.keys()),
        "ready_for_game": len([model for model in nlp.models.values() if model is not None]) >= 1
    }

# =============================================================================
# CONVERSATION AI ENDPOINTS
# =============================================================================

@app.post("/conversation/start", response_model=StartConversationResponse)
async def start_conversation(request: StartConversationRequest):
    # return "hi"
    """Start a new AI conversation session with custom prompt"""
    if not conversation_manager:
        raise HTTPException(
            status_code=503, 
            detail="Conversation AI not available - missing OPENAI_API_KEY"
        )

    try:
        conversation_id = await conversation_manager.start_conversation(
            user_id=request.user_id,
            language=request.language,
            name=request.name
        )

        return StartConversationResponse(
            conversation_id=conversation_id,
            message="Started conversation",
            language=request.language,
        )

    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@app.post("/conversation/message", response_model=ConversationResponse)
async def send_message(request: SendMessageRequest):
    """Send a message in an active conversation"""
    if not conversation_manager:
        raise HTTPException(
            status_code=503, 
            detail="Conversation AI not available - missing OPENAI_API_KEY"
        )
    
    try:
        response = await conversation_manager.send_message(
            conversation_id=request.conversation_id,
            user_message=request.message
        )
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.get("/conversation/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(conversation_id: str):
    """Get conversation history and state"""
    if not conversation_manager:
        raise HTTPException(
            status_code=503, 
            detail="Conversation AI not available - missing OPENAI_API_KEY"
        )

    conversation = conversation_manager.get_conversation_history(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationHistoryResponse(
        conversation=conversation,
        total_messages=conversation.total_messages,
        language=conversation.language,
        character_info=conversation.character_info,
        conversation_instructions=conversation.conversation_instructions,
        journal_words=conversation.journal_words
    )

@app.delete("/conversation/{conversation_id}")
async def end_conversation(conversation_id: str):
    """End and clean up a conversation"""
    if not conversation_manager:
        raise HTTPException(
            status_code=503, 
            detail="Conversation AI not available"
        )
    
    if conversation_id in conversation_manager.active_conversations:
        del conversation_manager.active_conversations[conversation_id]
        return {"message": "Conversation ended successfully"}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.get("/conversation/examples")
async def get_conversation_examples():
    """Get example conversation prompts"""
    return {
        "examples": [
            {
                "language": "es",
                "prompt": "I am an old man who will ask you how old you are",
                "description": "Simple age question roleplay"
            },
            {
                "language": "es", 
                "prompt": "I am a waiter at a restaurant and you are ordering food",
                "description": "Restaurant ordering scenario"
            },
            {
                "language": "es",
                "prompt": "I am asking for directions to the library",
                "description": "Asking for directions"
            },
            {
                "language": "ja",
                "prompt": "I am a shop clerk greeting customers",
                "description": "Shop greeting in Japanese"
            }
        ]
    }

# =============================================================================
# NLP ENDPOINTS
# =============================================================================

@app.post("/tokenize", response_model=TokenizeResponse)
async def tokenize_text(request: TokenizeRequest):
    """
    High-performance tokenization optimized for language learning games
    Provides rich morphological and grammatical information
    """
    start_time = time.time()
    

    try:
        language_model = nlp.load_language_model(request.language)
        doc = language_model(request.text)
        
        tokens = []
        for token in doc:
            morphology = None
            if request.include_morphology and token.morph:
                morphology = {str(key): str(value) for key, value in token.morph.to_dict().items()}
            
            # Optional dependency information for advanced language learning
            dep = None
            head_text = None
            if request.include_dependencies:
                dep = token.dep_
                head_text = token.head.text if token.head != token else None
            
            token_info = TokenInfo(
                text=token.text,
                lemma=token.lemma_ if request.include_lemma else None,
                pos=token.pos_ if request.include_pos else None,
                tag=token.tag_ if request.include_pos else None,
                morphology=morphology,
                dep=dep,
                head_text=head_text,
                is_alpha=token.is_alpha,
                is_digit=token.is_digit,
                is_punct=token.is_punct,
                is_space=token.is_space
            )
            tokens.append(token_info)
        
        sentences = [sent.text.strip() for sent in doc.sents]
        word_count = len([token for token in doc if not token.is_space and not token.is_punct])
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if processing_time > 100:  # Log slow requests for game optimization
            logger.warning(f"⚠️ Slow tokenization: {processing_time:.2f}ms for {len(request.text)} chars")
        
        return TokenizeResponse(
            tokens=tokens,
            sentences=sentences,
            language=request.language,
            word_count=word_count,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"💥 Error tokenizing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.post("/morphemes", response_model=MorphemeResponse)
async def extract_morphemes(request: MorphemeRequest):
    """
    Extract detailed morphological information optimized for language learning
    Perfect for understanding grammar patterns in Spanish and Japanese
    """
    try:
        return nlp.get_morphemes(request.text, request.language)
    except Exception as e:
        logger.error(f"💥 Error extracting morphemes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.get("/languages")
async def get_supported_languages():
    """Get language support status optimized for game"""
    return {
        "priority_languages": {
            lang: {
                "model": model_name,
                "loaded": nlp.models.get(lang) is not None,
                "status": "ready" if nlp.models.get(lang) is not None else "needs_download"
            }
            for lang, model_name in nlp.PRIORITY_LANGUAGES.items()
        },
        "all_supported": nlp.SUPPORTED_LANGUAGES,
        "currently_loaded": [lang for lang, model in nlp.models.items() if model is not None]
    }

@app.post("/preload/{language}")
async def preload_language_model(language: str):
    """Preload a specific language model for game optimization"""
    try:
        start_time = time.time()
        nlp.load_language_model(language)
        load_time = (time.time() - start_time) * 1000
        
        return {
            "language": language,
            "status": "loaded",
            "load_time_ms": round(load_time, 2),
            "message": f"🚀 Model {nlp.SUPPORTED_LANGUAGES[language]} ready for game!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preloading model: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)