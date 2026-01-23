FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./

# Copy data files (chroma_db and bm25 index)
COPY chroma_db/ ./chroma_db/
COPY bm25_index.pkl ./bm25_index.pkl

# Set environment variables for data paths
ENV CHROMA_PATH=/app/chroma_db
ENV BM25_PATH=/app/bm25_index.pkl

# Railway uses PORT env variable
ENV PORT=8000
EXPOSE 8000

# Run the server with Railway's PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
