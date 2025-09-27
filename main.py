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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Language models cache
nlp_models = {}

# Optimized for language learning game: Spanish and Japanese priority
PRIORITY_LANGUAGES = {
    "es": "es_core_news_sm",  # Spanish - primary
    "ja": "ja_core_news_sm",  # Japanese - primary
}

SUPPORTED_LANGUAGES = {
    "en": "en_core_web_sm",   # English - fallback/development
    "es": "es_core_news_sm",  # Spanish - primary
    "ja": "ja_core_news_sm",  # Japanese - primary
    "fr": "fr_core_news_sm",  # French - can be added later
    "de": "de_core_news_sm",  # German - can be added later
    "zh": "zh_core_web_sm",   # Chinese - can be added later
}

async def preload_priority_models():
    """Preload Spanish and Japanese models at startup for game performance"""
    logger.info("🚀 Preloading priority language models for game...")
    
    for lang, model_name in PRIORITY_LANGUAGES.items():
        try:
            start_time = time.time()
            nlp_models[lang] = spacy.load(model_name)
            load_time = time.time() - start_time
            logger.info(f"✅ Loaded {model_name} in {load_time:.2f}s")
        except OSError:
            logger.warning(f"⚠️ {model_name} not found - install with: python -m spacy download {model_name}")
            nlp_models[lang] = None
    
    # Warm up models with test text for even faster first requests
    if nlp_models.get("es"):
        nlp_models["es"]("Hola mundo")
        logger.info("🔥 Spanish model warmed up")
    
    if nlp_models.get("ja"):
        nlp_models["ja"]("こんにちは")
        logger.info("🔥 Japanese model warmed up")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await preload_priority_models()
    logger.info("🎮 Gloss NLP Backend ready for game!")
    yield
    # Shutdown
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title="Gloss NLP Backend - Game Optimized",
    description="High-performance NLP backend optimized for language learning games",
    version="2.1.0",
    lifespan=lifespan
)

# Configure CORS - optimized for game deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # Next.js dev
        "https://*.vercel.app",         # Vercel deployments
        "https://vercel.app",           # Vercel domain
        # Add your game domain here when deployed
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],      # Only what we need
    allow_headers=["*"],
)

def load_language_model(language: str):
    """Load and cache a SpaCy language model with game-optimized error handling"""
    if language not in nlp_models:
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400, 
                detail=f"Language '{language}' not supported. Supported: {list(SUPPORTED_LANGUAGES.keys())}"
            )
        
        model_name = SUPPORTED_LANGUAGES[language]
        try:
            start_time = time.time()
            nlp_models[language] = spacy.load(model_name)
            load_time = time.time() - start_time
            logger.info(f"📚 Loaded {model_name} in {load_time:.2f}s")
        except OSError:
            raise HTTPException(
                status_code=503,
                detail=f"Language model '{model_name}' not available. Install with: python -m spacy download {model_name}"
            )
    
    return nlp_models[language]

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

class MorphemeInfo(BaseModel):
    token_text: str
    lemma: str
    morphological_features: List[str]  # e.g., ["Tense:Past", "Number:Sing"]
    token_index: int

class MorphemeResponse(BaseModel):
    morphemes: List[MorphemeInfo]
    original_text: str
    language: str
    processing_time_ms: float
    
    # Legacy format for backward compatibility
    idx_to_morpheme: Dict[int, List[str]]

@app.get("/")
async def root():
    """Health check endpoint for game backend"""
    return {
        "message": "🎮 Gloss NLP Backend - Game Ready",
        "version": "2.1.0",
        "priority_languages": list(PRIORITY_LANGUAGES.keys()),
        "all_supported": list(SUPPORTED_LANGUAGES.keys()),
        "preloaded_models": [lang for lang, model in nlp_models.items() if model is not None],
        "features": ["morphology", "lemmatization", "game_optimized"]
    }

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    return {
        "status": "healthy",
        "preloaded_models": [lang for lang, model in nlp_models.items() if model is not None],
        "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        "priority_languages": list(PRIORITY_LANGUAGES.keys()),
        "ready_for_game": len([model for model in nlp_models.values() if model is not None]) >= 1
    }

@app.post("/tokenize", response_model=TokenizeResponse)
async def tokenize_text(request: TokenizeRequest):
    """
    High-performance tokenization optimized for language learning games
    Provides rich morphological and grammatical information
    """
    start_time = time.time()
    
    try:
        nlp = load_language_model(request.language)
        doc = nlp(request.text)
        
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
    start_time = time.time()
    
    try:
        nlp = load_language_model(request.language)
        doc = nlp(request.text)
        
        morphemes = []
        idx_to_morpheme = {}  # Legacy compatibility
        
        for token in doc:
            if token.is_space or token.is_punct:
                continue
            
            # Collect morphological features for language learning
            features = []
            if token.morph:
                for feature, value in token.morph.to_dict().items():
                    features.append(f"{feature}:{value}")
            
            morpheme_info = MorphemeInfo(
                token_text=token.text,
                lemma=token.lemma_,
                morphological_features=features,
                token_index=token.idx
            )
            morphemes.append(morpheme_info)
            
            # Legacy format for backward compatibility
            idx_to_morpheme[token.idx] = [token.lemma_] + features
        
        processing_time = (time.time() - start_time) * 1000
        
        if processing_time > 100:
            logger.warning(f"⚠️ Slow morpheme extraction: {processing_time:.2f}ms")
        
        return MorphemeResponse(
            morphemes=morphemes,
            original_text=request.text,
            language=request.language,
            processing_time_ms=round(processing_time, 2),
            idx_to_morpheme=idx_to_morpheme  # Legacy compatibility
        )
        
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
                "loaded": nlp_models.get(lang) is not None,
                "status": "ready" if nlp_models.get(lang) is not None else "needs_download"
            }
            for lang, model_name in PRIORITY_LANGUAGES.items()
        },
        "all_supported": SUPPORTED_LANGUAGES,
        "currently_loaded": [lang for lang, model in nlp_models.items() if model is not None]
    }

@app.post("/preload/{language}")
async def preload_language_model(language: str):
    """Preload a specific language model for game optimization"""
    try:
        start_time = time.time()
        load_language_model(language)
        load_time = (time.time() - start_time) * 1000
        
        return {
            "language": language,
            "status": "loaded",
            "load_time_ms": round(load_time, 2),
            "message": f"🚀 Model {SUPPORTED_LANGUAGES[language]} ready for game!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preloading model: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)