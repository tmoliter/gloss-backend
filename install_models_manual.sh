#!/bin/bash

echo "🔧 Manual SpaCy model installer (SSL workaround)"
echo "This downloads models without using pip's SSL"

cd nlp-backend
source venv/bin/activate

echo "📥 Downloading Spanish model manually..."
# Download directly from GitHub releases
curl -L -o es_core_news_sm-3.8.0.tar.gz \
  "https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.8.0/es_core_news_sm-3.8.0.tar.gz"

echo "📥 Downloading Japanese model manually..."  
curl -L -o ja_core_news_sm-3.8.0.tar.gz \
  "https://github.com/explosion/spacy-models/releases/download/ja_core_news_sm-3.8.0/ja_core_news_sm-3.8.0.tar.gz"

echo "📦 Installing models..."
pip install es_core_news_sm-3.8.0.tar.gz --no-deps
pip install ja_core_news_sm-3.8.0.tar.gz --no-deps

echo "🧹 Cleaning up..."
rm *.tar.gz

echo "✅ Models installed! Test with:"
echo "python -c \"import spacy; nlp = spacy.load('es_core_news_sm'); print('Spanish model loaded!')\""
echo "python -c \"import spacy; nlp = spacy.load('ja_core_news_sm'); print('Japanese model loaded!')\""