# Autography

> The open evidence of product management

An indexable chatbot for PM knowledge that returns citable evidence from curated sources.

## Data Sources

| Source | Status | Volume |
|--------|--------|--------|
| Lenny's Podcast | Ready ([GitHub](https://github.com/ChatPRD/lennys-podcast-transcripts)) | 269 episodes |
| Founders Podcast | Need transcription (Parakeet) | ~100 priority |
| David Senra Podcast | Need transcription | ~15 episodes |
| John Cutler | Need curation | ~1000 posts |
| Top 20 PM Books | EPUB preferred | 20 books |

## Tech Stack

- **Vector DB**: ChromaDB with hybrid search (RRF)
- **Transcription**: Parakeet MLX (local, free)
- **RAG**: LlamaIndex with citation tracking
- **Frontend**: Next.js 15 + Vercel AI SDK
- **Backend**: Python (FastAPI)

## Project Structure

```
autography/
├── data/
│   ├── lennys/            # Cloned transcript repo
│   ├── founders/          # Downloaded audio + transcripts
│   └── books/             # EPUB files
├── ingestion/
│   ├── batch_transcribe.py
│   ├── download_founders.py
│   └── chunk_and_embed.py
├── backend/
│   └── api/
├── frontend/
│   └── (Next.js)
└── plans/
```

## Quick Start

```bash
# 1. Clone Lenny's transcripts
git clone https://github.com/ChatPRD/lennys-podcast-transcripts.git data/lennys

# 2. Download priority Founders episodes
python ingestion/download_founders.py --priority 100 -o data/founders/audio

# 3. Transcribe with Parakeet
python ingestion/batch_transcribe.py data/founders/audio -o data/founders/transcripts

# 4. Ingest into ChromaDB
python ingestion/chunk_and_embed.py
```
