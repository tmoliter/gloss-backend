# Gloss NLP Backend - Deployment Guide

## Overview
High-performance NLP backend optimized for language learning games. Pre-loads Spanish and Japanese SpaCy models for <100ms response times during gameplay.

## 🎮 Game-Optimized Features
- **Pre-loaded models**: Spanish & Japanese models load at startup
- **Performance tracking**: Response time monitoring for game optimization  
- **Rich morphology**: Full grammatical analysis for language learning
- **Fallback support**: Graceful degradation if models unavailable

## 🚀 Quick Deployment Options

### Option 1: Railway (Recommended)
Railway is perfect for this backend - handles SpaCy models well and stays warm.

1. **Setup Railway:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   ```

2. **Deploy:**
   ```bash
   cd nlp-backend
   railway up
   ```

3. **Configure Environment:**
   - Railway automatically sets `PORT` environment variable
   - No additional configuration needed!

### Option 2: Render
1. Connect your GitHub repo to Render
2. Choose "Web Service"
3. Set build command: `pip install -r requirements.txt && python -m spacy download es_core_news_sm ja_core_news_sm en_core_web_sm`
4. Set start command: `python main.py`

### Option 3: Local Development
```bash
cd nlp-backend
chmod +x setup.sh
./setup.sh
```

## 📊 API Endpoints

### Health Check
```http
GET /health
```
Returns model loading status and performance metrics.

### Tokenization (Primary for game)
```http
POST /tokenize
Content-Type: application/json

{
  "text": "Me gusta aprender español",
  "language": "es",
  "include_morphology": true,
  "include_dependencies": false
}
```

### Morphological Analysis
```http
POST /morphemes
Content-Type: application/json

{
  "text": "私は日本語を勉強します",
  "language": "ja",
  "include_features": true
}
```

## ⚡ Performance Targets
- **Cold start**: <30s (model loading)
- **Warm requests**: <100ms (target achieved)
- **Memory usage**: ~500MB (with ES + JA models)

## 🔧 Configuration

### Environment Variables
```bash
PORT=8000                    # Server port
PYTHONUNBUFFERED=1          # Logging
```

### Game Integration
Update your Next.js frontend to point to the deployed backend:

```typescript
// lib/nlp-client.ts
const NLP_API_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-railway-domain.railway.app'
  : 'http://localhost:8000';
```

## 🎯 Language Learning Game Features

### Morphological Analysis
Perfect for showing users grammar breakdowns:
```json
{
  "morphemes": [
    {
      "token_text": "estudia",
      "lemma": "estudiar", 
      "morphological_features": [
        "Tense:Pres",
        "Person:3", 
        "Number:Sing"
      ]
    }
  ]
}
```

### Performance Monitoring
Track response times to optimize game experience:
```json
{
  "processing_time_ms": 45.2,
  "word_count": 5
}
```

## 🐛 Troubleshooting

### Models Not Loading
```bash
# Check if models are installed
python -c "import spacy; spacy.load('es_core_news_sm')"

# Reinstall if needed
python -m spacy download es_core_news_sm
```

### Slow Performance
- Check `/health` endpoint for model status
- Monitor `processing_time_ms` in responses
- Consider increasing server resources if consistently >100ms

### CORS Issues
Add your game domain to CORS origins in `main.py`:
```python
allow_origins=[
    "https://your-game.vercel.app",  # Add your domain
    "http://localhost:3000",
    "https://*.vercel.app",
]
```

## 📈 Scaling for Production

### Model Management
- Current: Spanish + Japanese (~100MB total)
- Future: Add languages dynamically as game expands
- Consider model caching strategies for multi-region deployment

### Performance Optimization  
- Use Railway's auto-scaling for traffic spikes
- Monitor response times via health endpoint
- Consider Redis caching for repeated text analysis

## 🎮 Integration with Next.js Game

Your Vercel-deployed Next.js app can seamlessly call this backend:

```typescript
// Example game integration
const analyzeUserMessage = async (text: string, language: string) => {
  const response = await fetch(`${NLP_API_URL}/tokenize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      text, 
      language, 
      include_morphology: true 
    })
  });
  
  const data = await response.json();
  console.log(`Analysis completed in ${data.processing_time_ms}ms`);
  return data;
};
```

This setup gives you production-ready NLP processing with game-optimized performance!