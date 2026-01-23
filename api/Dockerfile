FROM python:3.11-slim

WORKDIR /app

# Install only CPU version of PyTorch (much smaller than GPU version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code only (data comes from volume)
COPY api/ ./

# Data will be mounted from Railway volume at /data
# Set environment variables to point to volume
ENV CHROMA_PATH=/data/chroma_db
ENV BM25_PATH=/data/bm25_index.pkl

# Railway uses PORT env variable
ENV PORT=8000
EXPOSE 8000

# Run the server
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
