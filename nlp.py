

import time
import logging
from typing import Dict, List
from pydantic import BaseModel
import spacy
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Global language models cache

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
    idx_to_morpheme: Dict[int, List[str]]

    

class NaturalLanguageProcessor():
    """Handles NLP tasks using SpaCy with game-optimized error handling"""
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

    
    def __init__(self):
        self.models = {}

    def load_language_model(self, language: str) -> spacy.language.Language:
        """Load and cache a SpaCy language model with game-optimized error handling"""
        print("AAAA")
        if language not in self.models:
            print("BBBB")
            if language not in self.SUPPORTED_LANGUAGES:
                print("CCCC")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Language '{language}' not supported. Supported: {list(self.SUPPORTED_LANGUAGES.keys())}"
                )
            model_name = self.SUPPORTED_LANGUAGES[language]
            try:
                start_time = time.time()
                self.models[language] = spacy.load(model_name)
                load_time = time.time() - start_time
                logger.info(f"📚 Loaded {model_name} in {load_time:.2f}s")
            except OSError:
                raise HTTPException(
                    status_code=503,
                    detail=f"Language model '{model_name}' not available. Install with: python -m spacy download {model_name}"
                )
        
        return self.models[language]

    def get_morphemes(self, text: str, language: str):
        print(f"{text} ----- {language}")
        start_time = time.time()

        print(1)
        language_model = self.load_language_model(language)
        print(2)
        doc = language_model(text)
        print(3)
        morphemes = []
        idx_to_morpheme = {}  # Legacy compatibility
        
        for token in doc:
            print("AY!")
            print(token)
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
            original_text=text,
            language=language,
            processing_time_ms=round(processing_time, 2),
            idx_to_morpheme=idx_to_morpheme  # Legacy compatibility
        )
