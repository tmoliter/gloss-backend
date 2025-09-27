#!/bin/bash

# Setup script for Gloss NLP Backend - Game Optimized Version

echo "🎮 Setting up Gloss NLP Backend for Language Learning Game..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download priority language models for game performance
echo "� Downloading priority language models for game..."
echo "This may take a few minutes but ensures fast game startup..."

# Spanish (PRIMARY for game)
echo "🇪🇸 Downloading Spanish model..."
python -m spacy download es_core_news_sm

# Japanese (PRIMARY for game)
echo "🇯🇵 Downloading Japanese model..."
python -m spacy download ja_core_news_sm

# English (for development/fallback)
echo "🇺🇸 Downloading English model..."
python -m spacy download en_core_web_sm

# Test the models to ensure they work
echo "🧪 Testing language models..."
python -c "
import spacy
print('Testing Spanish model...')
nlp_es = spacy.load('es_core_news_sm')
doc = nlp_es('Hola mundo')
print(f'✅ Spanish: {doc[0].text} -> {doc[0].lemma_} ({doc[0].pos_})')

print('Testing Japanese model...')  
nlp_ja = spacy.load('ja_core_news_sm')
doc = nlp_ja('こんにちは')
print(f'✅ Japanese: {doc[0].text} -> {doc[0].lemma_} ({doc[0].pos_})')

print('✅ All models ready for game!')
"

echo "🎯 Game-optimized setup complete!"
echo ""
echo "🎮 Your language learning game backend is ready!"
echo ""
echo "To run locally:"
echo "  cd nlp-backend"
echo "  source venv/bin/activate"  
echo "  python main.py"
echo ""
echo "🚀 For Railway deployment:"
echo "  1. Push to GitHub"
echo "  2. Connect Railway to your repo"
echo "  3. Railway will auto-deploy using Dockerfile"
echo ""
echo "📊 API endpoints:"
echo "  Health: http://localhost:8000/health"
echo "  Tokenize: POST http://localhost:8000/tokenize" 
echo "  Morphemes: POST http://localhost:8000/morphemes"
echo "  Languages: GET http://localhost:8000/languages"
echo ""
echo "🎯 Optimized for Spanish & Japanese language learning!"