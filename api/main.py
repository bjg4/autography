"""
FastAPI backend for Autography PM knowledge base search.

Provides REST API endpoints for hybrid search (semantic + BM25).
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

# Load .env file if it exists
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from routers import search, chat


def init_phoenix_tracing():
    """Initialize Arize Phoenix for LLM observability."""
    phoenix_api_key = os.environ.get("PHOENIX_API_KEY")
    if not phoenix_api_key:
        print("PHOENIX_API_KEY not set - LLM tracing disabled")
        return False

    try:
        from phoenix.otel import register
        from openinference.instrumentation.anthropic import AnthropicInstrumentor

        # Configure Phoenix endpoint
        endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "https://app.phoenix.arize.com")
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = endpoint
        os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={phoenix_api_key}"

        # Register tracer and instrument Anthropic
        tracer_provider = register(project_name="autography")
        AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)

        print(f"Phoenix tracing enabled → {endpoint}")
        return True
    except ImportError as e:
        print(f"Phoenix packages not installed: {e}")
        return False
    except Exception as e:
        print(f"Phoenix initialization failed: {e}")
        return False

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize observability on startup. Search engine loads lazily."""
    # Initialize LLM observability first (before any Anthropic client is used)
    init_phoenix_tracing()

    # Configure paths for lazy loading (search engine loads on first request)
    chroma_path = os.environ.get('CHROMA_PATH', str(Path(__file__).parent.parent / 'chroma_db'))
    bm25_path = os.environ.get('BM25_PATH', str(Path(__file__).parent.parent / 'bm25_index.pkl'))

    print(f"Server starting (search engine will load on first request)...")
    print(f"  Chroma path: {chroma_path}")
    print(f"  BM25 path: {bm25_path}")

    # Initialize paths but don't load yet (lazy=True)
    search.init_search_engine(chroma_path, bm25_path, lazy=True)

    yield

    # Cleanup (if needed)
    print("Shutting down...")


app = FastAPI(
    title="Autography Search API",
    description="Search the PM knowledge base using hybrid semantic + keyword search",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration
allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
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
@limiter.limit("60/minute")
async def health(request: Request):
    """Health check endpoint."""
    doc_count = search.get_document_count()
    return {
        "status": "ok",
        "search_ready": doc_count > 0,
        "documents": doc_count
    }
