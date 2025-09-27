# Gloss NLP Backend

A minimal FastAPI backend for morpheme and word tokenization using SpaCy, designed to work with the Gloss text-based adventure game.

## Features

- **Multi-language support**: English, Spanish, French, German, Japanese, Chinese
- **Word tokenization**: Break text into tokens with linguistic information
- **Morpheme extraction**: Extract morphemes and morphological features
- **RESTful API**: Easy integration with Next.js frontend
- **CORS enabled**: Works with web applications
- **Fast**: Caches language models for performance

## Setup

### 1. Create Virtual Environment

```bash
cd nlp-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Language Models

```bash
# Download language models you need
python -m spacy download en_core_web_sm  # English
python -m spacy download es_core_news_sm # Spanish
python -m spacy download fr_core_news_sm # French
python -m spacy download de_core_news_sm # German
python -m spacy download ja_core_news_sm # Japanese
python -m spacy download zh_core_web_sm  # Chinese
```

### 4. Run the Server

```bash
python main.py
# Or with uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health with loaded models
- `GET /languages` - List supported and loaded languages

### Text Processing
- `POST /tokenize` - Tokenize text with linguistic information
- `POST /morphemes` - Extract morphemes from text

## Example Usage

### Tokenize Text
```bash
curl -X POST "http://localhost:8000/tokenize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world! How are you?",
    "language": "en",
    "include_morphology": true
  }'
```

### Extract Morphemes
```bash
curl -X POST "http://localhost:8000/morphemes" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "running quickly",
    "language": "en"
  }'
```

## Deployment Options

### Railway
```bash
# Add railway.json to deploy
railway login
railway init
railway up
```

### Render
- Connect your GitHub repo
- Set build command: `pip install -r requirements.txt && python -c "import spacy; spacy.cli.download('en_core_web_sm')"`
- Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### DigitalOcean App Platform
- Connect repo
- Add environment variables if needed
- Deploy!

## Integration with Next.js

Add to your Next.js app:

```typescript
// lib/nlp-client.ts
const NLP_API_BASE = process.env.NEXT_PUBLIC_NLP_API_URL || 'http://localhost:8000';

export async function tokenizeText(text: string, language: string = 'en') {
  const response = await fetch(`${NLP_API_BASE}/tokenize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language, include_morphology: true })
  });
  return response.json();
}

export async function extractMorphemes(text: string, language: string = 'en') {
  const response = await fetch(`${NLP_API_BASE}/morphemes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language })
  });
  return response.json();
}
```

## Language Support

| Language | Code | Model | Status |
|----------|------|-------|--------|
| English | en | en_core_web_sm | ✅ |
| Spanish | es | es_core_news_sm | ✅ |
| French | fr | fr_core_news_sm | ✅ |
| German | de | de_core_news_sm | ✅ |
| Japanese | ja | ja_core_news_sm | ✅ |
| Chinese | zh | zh_core_web_sm | ✅ |

## Performance Notes

- Language models are cached in memory after first use
- Consider using a reverse proxy (nginx) for production
- For high traffic, consider horizontal scaling

## License

MIT License