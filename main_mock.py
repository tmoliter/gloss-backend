from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gloss NLP Backend",
    description="A minimal backend for morpheme and word tokenization using SpaCy",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Language models cache
models = {}

# Mock tokenization for testing without models
def mock_tokenize(text: str, language: str):
    """Basic tokenization using simple splitting - for testing without spaCy models"""
    import re
    
    # Basic word splitting
    words = re.findall(r'\b\w+\b', text)
    punctuation = re.findall(r'[^\w\s]', text)
    
    tokens = []
    for word in words:
        tokens.append({
            "text": word,
            "lemma": word.lower(),
            "pos": "NOUN" if len(word) > 4 else "DET",  # Mock POS tagging
            "tag": "NN" if len(word) > 4 else "DT",
            "morphology": {"Number": "Sing"},
            "is_alpha": word.isalpha(),
            "is_digit": word.isdigit(),
            "is_punct": False,
            "is_space": False
        })
    
    for punct in punctuation:
        tokens.append({
            "text": punct,
            "lemma": punct,
            "pos": "PUNCT",
            "tag": ".",
            "morphology": {},
            "is_alpha": False,
            "is_digit": False,
            "is_punct": True,
            "is_space": False
        })
    
    sentences = text.split('. ')
    word_count = len(words)
    
    return {
        "tokens": tokens,
        "sentences": sentences,
        "language": language,
        "word_count": word_count
    }

# Request/Response models
class TokenizeRequest(BaseModel):
    text: str
    language: str = "en"
    include_morphology: bool = False
    include_pos: bool = True
    include_lemma: bool = True

class MorphemeRequest(BaseModel):
    text: str
    language: str = "en"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Gloss NLP Backend is running (mock mode - no spaCy models loaded)",
        "supported_languages": ["en", "es", "ja"],
        "note": "Using mock tokenization until spaCy models are installed"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "mode": "mock",
        "loaded_models": list(models.keys()),
        "note": "Run with spaCy models for full functionality"
    }

@app.post("/tokenize")
async def tokenize_text(request: TokenizeRequest):
    """
    Tokenize text into words/tokens (mock version)
    """
    try:
        # For now, use mock tokenization
        result = mock_tokenize(request.text, request.language)
        return result
        
    except Exception as e:
        logger.error(f"Error tokenizing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.post("/morphemes")
async def extract_morphemes(request: MorphemeRequest):
    """
    Extract morphemes from text (mock version)
    """
    try:
        # Simple morpheme extraction - split on common patterns
        import re
        words = re.findall(r'\b\w+\b', request.text)
        
        morphemes = []
        for word in words:
            if len(word) > 6:
                # Mock: split longer words into root + suffix
                morphemes.extend([word[:-2], word[-2:]])
            else:
                morphemes.append(word)
        
        return {
            "morphemes": morphemes,
            "original_text": request.text,
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Error extracting morphemes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": {
            "en": "en_core_web_sm (not loaded - using mock)",
            "es": "es_core_news_sm (not loaded - using mock)",
            "ja": "ja_core_news_sm (not loaded - using mock)"
        },
        "loaded": list(models.keys()),
        "note": "Install spaCy models for full functionality"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Gloss NLP Backend in MOCK mode...")
    print("📝 This version uses basic tokenization until spaCy models are installed")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)