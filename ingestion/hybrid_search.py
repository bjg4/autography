#!/usr/bin/env python3
"""
Hybrid search combining semantic (Chroma) and keyword (BM25) search.

Uses Reciprocal Rank Fusion (RRF) to combine rankings:
    RRF(d) = Σ 1/(k + rank(d))
    where k=60 (standard constant)
"""

import pickle
from pathlib import Path
from typing import Optional

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


class HybridSearch:
    """Hybrid semantic + BM25 search over the PM knowledge base."""

    def __init__(
        self,
        chroma_path: str = None,
        model_name: str = 'all-MiniLM-L6-v2',
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        k: int = 60  # RRF constant
    ):
        """Initialize hybrid search.

        Args:
            chroma_path: Path to Chroma DB directory
            model_name: Sentence transformer model name
            semantic_weight: Weight for semantic search (0-1)
            bm25_weight: Weight for BM25 search (0-1)
            k: RRF constant (default 60)
        """
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        self.k = k

        # Paths
        if chroma_path is None:
            chroma_path = str(Path(__file__).parent.parent / 'chroma_db')

        # Initialize Chroma
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_collection('autography')

        # Load embedding model
        self.model = SentenceTransformer(model_name)

        # Initialize BM25 index
        self._init_bm25()

    def _init_bm25(self):
        """Initialize BM25 index from Chroma documents."""
        bm25_cache = Path(__file__).parent.parent / 'bm25_index.pkl'

        # Try to load cached index
        if bm25_cache.exists():
            with open(bm25_cache, 'rb') as f:
                cache = pickle.load(f)
                self.bm25 = cache['bm25']
                self.doc_ids = cache['doc_ids']
                self.doc_texts = cache['doc_texts']
                self.doc_metadatas = cache['doc_metadatas']
                print(f"Loaded BM25 index from cache ({len(self.doc_ids)} docs)")
                return

        # Build index from Chroma
        print("Building BM25 index...")
        all_docs = self.collection.get(include=['documents', 'metadatas'])

        self.doc_ids = all_docs['ids']
        self.doc_texts = all_docs['documents']
        self.doc_metadatas = all_docs['metadatas']

        # Tokenize for BM25
        tokenized_corpus = [doc.lower().split() for doc in self.doc_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Cache index
        with open(bm25_cache, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'doc_ids': self.doc_ids,
                'doc_texts': self.doc_texts,
                'doc_metadatas': self.doc_metadatas
            }, f)
        print(f"Built and cached BM25 index ({len(self.doc_ids)} docs)")

    def _semantic_search(self, query: str, n: int) -> list[tuple[str, float]]:
        """Perform semantic search via Chroma.

        Returns: List of (doc_id, score) tuples
        """
        query_embedding = self.model.encode([query])[0].tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=['distances']
        )

        # Convert distances to scores (Chroma returns L2 distance for cosine)
        # Lower distance = better match, so we invert
        scored = []
        for doc_id, distance in zip(results['ids'][0], results['distances'][0]):
            score = 1 / (1 + distance)  # Convert distance to similarity
            scored.append((doc_id, score))

        return scored

    def _bm25_search(self, query: str, n: int) -> list[tuple[str, float]]:
        """Perform BM25 keyword search.

        Returns: List of (doc_id, score) tuples
        """
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Get top N
        scored_docs = [(self.doc_ids[i], scores[i]) for i in range(len(scores))]
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return scored_docs[:n]

    def _reciprocal_rank_fusion(
        self,
        semantic_results: list[tuple[str, float]],
        bm25_results: list[tuple[str, float]]
    ) -> list[tuple[str, float]]:
        """Combine rankings using Reciprocal Rank Fusion.

        RRF(d) = Σ weight * 1/(k + rank(d))
        """
        scores = {}

        # Add semantic scores
        for rank, (doc_id, _) in enumerate(semantic_results, 1):
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += self.semantic_weight * (1 / (self.k + rank))

        # Add BM25 scores
        for rank, (doc_id, _) in enumerate(bm25_results, 1):
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += self.bm25_weight * (1 / (self.k + rank))

        # Sort by combined score
        combined = [(doc_id, score) for doc_id, score in scores.items()]
        combined.sort(key=lambda x: x[1], reverse=True)

        return combined

    def search(
        self,
        query: str,
        n_results: int = 5,
        source_type: Optional[str] = None,
        author: Optional[str] = None
    ) -> list[dict]:
        """Perform hybrid search.

        Args:
            query: Search query
            n_results: Number of results to return
            source_type: Filter by source type (essay, book_chapter, podcast_transcript)
            author: Filter by author name

        Returns:
            List of result dicts with id, content, metadata, score
        """
        # Get more candidates for RRF
        n_candidates = n_results * 3

        # Run both searches
        semantic_results = self._semantic_search(query, n_candidates)
        bm25_results = self._bm25_search(query, n_candidates)

        # Combine with RRF
        combined = self._reciprocal_rank_fusion(semantic_results, bm25_results)

        # Build results
        results = []
        for doc_id, score in combined[:n_results * 2]:  # Get extra for filtering
            idx = self.doc_ids.index(doc_id)
            metadata = self.doc_metadatas[idx]

            # Apply filters
            if source_type and metadata.get('source_type') != source_type:
                continue
            if author and author.lower() not in metadata.get('author', '').lower():
                continue

            results.append({
                'id': doc_id,
                'content': self.doc_texts[idx],
                'metadata': metadata,
                'score': score
            })

            if len(results) >= n_results:
                break

        return results

    def semantic_only(self, query: str, n_results: int = 5) -> list[dict]:
        """Semantic search only (for comparison)."""
        results = self._semantic_search(query, n_results)

        output = []
        for doc_id, score in results:
            idx = self.doc_ids.index(doc_id)
            output.append({
                'id': doc_id,
                'content': self.doc_texts[idx],
                'metadata': self.doc_metadatas[idx],
                'score': score
            })

        return output

    def bm25_only(self, query: str, n_results: int = 5) -> list[dict]:
        """BM25 search only (for comparison)."""
        results = self._bm25_search(query, n_results)

        output = []
        for doc_id, score in results:
            idx = self.doc_ids.index(doc_id)
            output.append({
                'id': doc_id,
                'content': self.doc_texts[idx],
                'metadata': self.doc_metadatas[idx],
                'score': score
            })

        return output


def main():
    """Test hybrid search."""
    print("Initializing hybrid search...")
    search = HybridSearch()

    test_queries = [
        "What is a feature factory?",
        "How to write a one-pager",
        "Six week cycles shaping",
        "Cutler NPS",
        "customer interviews discovery",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        results = search.search(query, n_results=3)

        for i, r in enumerate(results, 1):
            meta = r['metadata']
            print(f"\n{i}. {meta['title']}")
            print(f"   Author: {meta['author']} | Type: {meta['source_type']}")
            print(f"   Score: {r['score']:.4f} | Chars: {meta['char_count']}")
            # Show snippet
            snippet = r['content'][:200].replace('\n', ' ')
            print(f"   Snippet: {snippet}...")


if __name__ == '__main__':
    main()
