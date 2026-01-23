FROM python:3.11-slim

WORKDIR /app

# Install only CPU version of PyTorch (much smaller than GPU version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./

# Copy and extract compressed data
COPY data.tar.gz .
RUN tar -xzf data.tar.gz && rm data.tar.gz

# Set environment variables for data paths
ENV CHROMA_PATH=/app/chroma_db
ENV BM25_PATH=/app/bm25_index.pkl

# Railway uses PORT env variable
ENV PORT=8000
EXPOSE 8000

# Run the server
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
