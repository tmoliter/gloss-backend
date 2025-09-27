# Optimized Dockerfile for language learning game NLP backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for SpaCy models
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download priority language models for game performance
# Spanish and Japanese are preloaded for instant game startup
RUN python -m spacy download es_core_news_sm
RUN python -m spacy download ja_core_news_sm  
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port (Railway will set PORT env var)
EXPOSE $PORT

# Health check optimized for game backend
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Use main.py with game optimizations
CMD python main.py