# feat: Hybrid Retrieval System for PM Knowledge Base

Build a hybrid retrieval system that indexes all PM content (posts, transcripts, books) and enables semantic + keyword search.

## Overview

Transform the curated PM knowledge base into a searchable system using:
- Markdown files as source of truth
- Chroma for vector storage + hybrid search
- BGE-M3 for embeddings (with Voyage-3 upgrade path)
- Full-document retrieval for posts, chapter-level for books

## Problem Statement

We have 365+ high-quality PM artifacts across blog posts, podcast transcripts, and books. Currently they're just files—no way to query "What does Cutler say about feature factories?" and get relevant passages with citations.

## Proposed Solution

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Source Files (Markdown)               │
│  /data/{author}/posts/*.md                              │
│  /data/books/extracted/{book}/*.md                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Indexing Pipeline                      │
│  1. Parse YAML frontmatter → metadata                   │
│  2. Extract content → text                              │
│  3. BGE-M3 → dense + sparse embeddings                  │
│  4. Store in Chroma                                     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Chroma Collection                      │
│  documents: [markdown content]                          │
│  embeddings: [BGE-M3 dense vectors]                     │
│  metadatas: [{author, source_type, date, ...}]          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Query Pipeline                         │
│  1. Hybrid search (70% semantic / 30% BM25)             │
│  2. Metadata filtering (optional)                       │
│  3. Return top-k full documents                         │
│  4. Claude synthesizes answer with citations            │
└─────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Book Extraction (This Session)

**Goal:** Extract Shape Up PDF to markdown chapters as proof of concept.

**Tasks:**
- [x] Install extraction tool: `pip install pymupdf4llm` (marker-pdf requires Python 3.10+)
- [x] Extract Shape Up to `/data/books/extracted/shape-up/`
- [x] Verify chapter structure and content quality (40 chapters, 191k chars)
- [x] Add YAML frontmatter to each chapter
- [x] Document extraction process in decision log

**Files:**
- `ingestion/extract_book.py` - Book extraction script (created)
- `/data/books/extracted/shape-up/ch*.md` - 40 extracted chapters
- `/data/books/extracted/shape-up/full-book.md` - Complete book as single file

### Phase 2: Indexing Pipeline

**Goal:** Index all markdown content into Chroma with hybrid search.

**Tasks:**
- [ ] Install dependencies: `pip install chromadb sentence-transformers rank-bm25`
- [ ] Create indexing script that:
  - Walks `/data` directory for all `.md` files
  - Parses YAML frontmatter
  - Generates BGE-M3 embeddings
  - Stores in Chroma with metadata
- [ ] Build BM25 index alongside vector index
- [ ] Test basic retrieval

**Files:**
- `ingestion/index_corpus.py` - Main indexing script
- `ingestion/hybrid_search.py` - Search implementation

### Phase 3: Query Interface

**Goal:** Simple CLI to test retrieval quality.

**Tasks:**
- [ ] Create query script that:
  - Takes natural language query
  - Performs hybrid search
  - Returns top-k documents with metadata
  - Formats for Claude consumption
- [ ] Test 20 representative queries
- [ ] Measure retrieval quality (manual review)

**Files:**
- `query.py` - CLI query interface

### Phase 4: Extract Remaining Books

**Goal:** Extract all 9 PM books to markdown.

**Tasks:**
- [ ] Extract each book using marker-pdf
- [ ] Manual review of chapter boundaries
- [ ] Add consistent frontmatter
- [ ] Re-index corpus

**Books:**
1. Shape Up (Phase 1 PoC) ✓
2. Inspired - Marty Cagan
3. Continuous Discovery Habits - Teresa Torres
4. The Mom Test - Rob Fitzpatrick
5. High Output Management - Andy Grove
6. The Hard Thing About Hard Things - Ben Horowitz
7. Good Strategy Bad Strategy - Richard Rumelt
8. The Lean Startup - Eric Ries
9. Design of Everyday Things - Don Norman

## Acceptance Criteria

### Phase 1 (Book Extraction) ✓
- [x] Shape Up extracted to 10+ chapter files (40 chapters)
- [x] Each chapter has valid YAML frontmatter
- [x] Content is readable, code blocks preserved
- [x] Extraction process documented in decision log

### Phase 2 (Indexing)
- [ ] All 365+ posts indexed in Chroma
- [ ] Shape Up chapters indexed
- [ ] Hybrid search returns results
- [ ] Metadata filtering works

### Phase 3 (Query Interface)
- [ ] Can query in natural language
- [ ] Returns relevant documents
- [ ] Shows source attribution
- [ ] Sub-second response time

## Technical Considerations

### Dependencies

```txt
# requirements.txt additions
marker-pdf>=1.0.0
chromadb>=1.4.0
sentence-transformers>=3.0.0
FlagEmbedding>=1.2.0
rank-bm25>=0.2.2
```

### Performance

- Indexing: ~2-5 minutes for full corpus
- Query: <500ms for hybrid search
- Storage: ~50MB for Chroma DB

### Risks

| Risk | Mitigation |
|------|------------|
| marker-pdf fails on some PDFs | Fallback to pymupdf4llm |
| BGE-M3 quality insufficient | Upgrade to Voyage-3 |
| Chapter detection misses boundaries | Manual review + correction |

## Success Metrics

1. **Retrieval quality**: 8/10 queries return relevant top-3 results
2. **Coverage**: All curated content is searchable
3. **Attribution**: Every result traces to source file
4. **Latency**: <1s for query response

## References

- [Decision Log](/docs/decision-log.md) - Architecture decisions
- [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [Chroma Hybrid Search](https://docs.trychroma.com/guides/build/agentic-search)
- [Cursor Semantic Search](https://cursor.com/blog/semsearch)
- [marker-pdf GitHub](https://github.com/datalab-to/marker)

---

*Created: 2026-01-19*
