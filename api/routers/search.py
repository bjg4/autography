"""
Search router for the Autography API.

Provides endpoints for hybrid search with filters.
"""

import pickle
from pathlib import Path
from typing import Optional

import chromadb
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

router = APIRouter(prefix="/api", tags=["search"])

# Global search engine instance
_search_engine: Optional["HybridSearch"] = None


class SearchRequest(BaseModel):
    """Search request body."""
    query: str = Field(..., min_length=1, description="Search query")
    n_results: int = Field(default=10, ge=1, le=50, description="Number of results")
    source_type: Optional[str] = Field(default=None, description="Filter by source type")
    author: Optional[str] = Field(default=None, description="Filter by author")
    mode: str = Field(default="hybrid", description="Search mode: hybrid, semantic, bm25")


class SearchResult(BaseModel):
    """Single search result."""
    id: str
    title: str
    author: str
    source_type: str
    score: float
    snippet: str
    metadata: dict


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    total: int
    results: list[SearchResult]


class SourcesResponse(BaseModel):
    """Available sources and stats."""
    source_types: list[str]
    authors: list[str]
    stats: dict


class HybridSearch:
    """Hybrid semantic + BM25 search over the PM knowledge base."""

    def __init__(
        self,
        chroma_path: str,
        bm25_path: str,
        model_name: str = 'all-MiniLM-L6-v2',
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        k: int = 60
    ):
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        self.k = k

        # Initialize Chroma
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_collection('autography')

        # Load embedding model
        self.model = SentenceTransformer(model_name)

        # Load BM25 index
        self._load_bm25(bm25_path)

    def _load_bm25(self, bm25_path: str):
        """Load BM25 index from pickle file."""
        with open(bm25_path, 'rb') as f:
            cache = pickle.load(f)
            self.bm25 = cache['bm25']
            self.doc_ids = cache['doc_ids']
            self.doc_texts = cache['doc_texts']
            self.doc_metadatas = cache['doc_metadatas']
        print(f"Loaded BM25 index ({len(self.doc_ids)} docs)")

    def _semantic_search(self, query: str, n: int) -> list[tuple[str, float]]:
        """Perform semantic search via Chroma."""
        query_embedding = self.model.encode([query])[0].tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=['distances']
        )

        scored = []
        for doc_id, distance in zip(results['ids'][0], results['distances'][0]):
            score = 1 / (1 + distance)
            scored.append((doc_id, score))

        return scored

    def _bm25_search(self, query: str, n: int) -> list[tuple[str, float]]:
        """Perform BM25 keyword search."""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        scored_docs = [(self.doc_ids[i], scores[i]) for i in range(len(scores))]
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return scored_docs[:n]

    def _reciprocal_rank_fusion(
        self,
        semantic_results: list[tuple[str, float]],
        bm25_results: list[tuple[str, float]]
    ) -> list[tuple[str, float]]:
        """Combine rankings using Reciprocal Rank Fusion."""
        scores = {}

        for rank, (doc_id, _) in enumerate(semantic_results, 1):
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += self.semantic_weight * (1 / (self.k + rank))

        for rank, (doc_id, _) in enumerate(bm25_results, 1):
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += self.bm25_weight * (1 / (self.k + rank))

        combined = [(doc_id, score) for doc_id, score in scores.items()]
        combined.sort(key=lambda x: x[1], reverse=True)

        return combined

    def search(
        self,
        query: str,
        n_results: int = 10,
        source_type: Optional[str] = None,
        source_types: Optional[list[str]] = None,
        author: Optional[str] = None,
        authors: Optional[list[str]] = None,
        mode: str = "hybrid",
        diversify: bool = True
    ) -> list[dict]:
        """Perform search with optional filters and diversity."""
        n_candidates = n_results * 5  # Get more candidates for diversity

        if mode == "semantic":
            ranked = self._semantic_search(query, n_candidates)
        elif mode == "bm25":
            ranked = self._bm25_search(query, n_candidates)
        else:
            semantic_results = self._semantic_search(query, n_candidates)
            bm25_results = self._bm25_search(query, n_candidates)
            ranked = self._reciprocal_rank_fusion(semantic_results, bm25_results)

        results = []
        seen_authors = {}  # Track how many results per author
        seen_sources = {}  # Track how many results per source title

        for doc_id, score in ranked:
            idx = self.doc_ids.index(doc_id)
            metadata = self.doc_metadatas[idx]

            # Single source_type filter (backwards compat)
            if source_type and metadata.get('source_type') != source_type:
                continue
            # Multiple source_types filter
            if source_types and metadata.get('source_type') not in source_types:
                continue
            # Single author filter (backwards compat)
            if author and author.lower() not in metadata.get('author', '').lower():
                continue
            # Multiple authors filter
            if authors:
                doc_author = metadata.get('author', '').lower()
                if not any(a.lower() in doc_author for a in authors):
                    continue

            # Diversity: limit results per author/source
            if diversify:
                doc_author = metadata.get('author', 'Unknown')
                doc_source = metadata.get('title', '') or metadata.get('book_title', '')

                author_count = seen_authors.get(doc_author, 0)
                source_count = seen_sources.get(doc_source, 0)

                # Allow max 3 from same author, max 2 from same source
                if author_count >= 3:
                    continue
                if source_count >= 2:
                    continue

                seen_authors[doc_author] = author_count + 1
                seen_sources[doc_source] = source_count + 1

            results.append({
                'id': doc_id,
                'content': self.doc_texts[idx],
                'metadata': metadata,
                'score': score
            })

            if len(results) >= n_results:
                break

        return results

    def get_sources(self) -> dict:
        """Get available source types and authors."""
        source_types = set()
        authors = set()

        for meta in self.doc_metadatas:
            if meta.get('source_type'):
                source_types.add(meta['source_type'])
            if meta.get('author'):
                authors.add(meta['author'])

        return {
            'source_types': sorted(source_types),
            'authors': sorted(authors),
            'stats': {
                'total_documents': len(self.doc_ids)
            }
        }


def init_search_engine(chroma_path: str, bm25_path: str):
    """Initialize the global search engine."""
    global _search_engine
    _search_engine = HybridSearch(chroma_path, bm25_path)


def get_document_count() -> int:
    """Get total document count."""
    if _search_engine is None:
        return 0
    return len(_search_engine.doc_ids)


def get_search_engine() -> HybridSearch:
    """Get the search engine instance."""
    if _search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    return _search_engine


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search the knowledge base."""
    engine = get_search_engine()

    results = engine.search(
        query=request.query,
        n_results=request.n_results,
        source_type=request.source_type,
        author=request.author,
        mode=request.mode
    )

    formatted_results = []
    for r in results:
        meta = r['metadata']
        snippet = r['content'][:500].replace('\n', ' ').strip()
        if len(r['content']) > 500:
            snippet += '...'

        formatted_results.append(SearchResult(
            id=r['id'],
            title=meta.get('title', 'Untitled'),
            author=meta.get('author', 'Unknown'),
            source_type=meta.get('source_type', 'unknown'),
            score=r['score'],
            snippet=snippet,
            metadata=meta
        ))

    return SearchResponse(
        query=request.query,
        total=len(formatted_results),
        results=formatted_results
    )


@router.get("/sources", response_model=SourcesResponse)
async def get_sources():
    """Get available sources and stats."""
    engine = get_search_engine()
    sources = engine.get_sources()

    return SourcesResponse(
        source_types=sources['source_types'],
        authors=sources['authors'],
        stats=sources['stats']
    )
