"""
FastAPI backend for Autography PM knowledge base search.

Provides REST API endpoints for hybrid search (semantic + BM25).
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Load .env file if it exists
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from routers import search, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load search engine on startup."""
    # Get paths from environment or use defaults
    chroma_path = os.environ.get('CHROMA_PATH', str(Path(__file__).parent.parent / 'chroma_db'))
    bm25_path = os.environ.get('BM25_PATH', str(Path(__file__).parent.parent / 'bm25_index.pkl'))

    print(f"Loading search engine...")
    print(f"  Chroma path: {chroma_path}")
    print(f"  BM25 path: {bm25_path}")

    search.init_search_engine(chroma_path, bm25_path)
    print(f"Search engine loaded with {search.get_document_count()} documents")

    yield

    # Cleanup (if needed)
    print("Shutting down...")


app = FastAPI(
    title="Autography Search API",
    description="Search the PM knowledge base using hybrid semantic + keyword search",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Autography Search API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "documents": search.get_document_count()
    }
