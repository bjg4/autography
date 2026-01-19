# Autography v3: Simplified Architecture

> Key insight: Start simpler. Add complexity only when you have evidence you need it.

## Research Summary

### Do We Need Chunking?

**Yes, but it depends on corpus size.**

| Corpus Size | Chunking Needed? | Approach |
|-------------|------------------|----------|
| < 100 docs | No | Embed full documents, retrieve top-k, feed to long-context LLM |
| 100-10K docs | Yes, but smart | "Small-to-big" - index chunks, retrieve parents |
| > 10K docs | Yes | Traditional chunked RAG with reranking |

**Our corpus**: ~500 sources (300 Lenny's + 9 David Senra + 50 Cutler + 9 books + Founders later)

**Recommendation**: Use **small-to-big retrieval**:
- Index 300-500 word chunks for retrieval precision
- Link chunks to parent documents
- Feed full transcript sections to Claude's 200K context

### Best Embedding Model

| Model | Quality | Cost | Self-Hosted? |
|-------|---------|------|--------------|
| **Voyage-3-large** | Best | $0.12/M tokens | No |
| **Cohere embed-v4** | Excellent | $0.10/M tokens | No |
| **BGE-M3** | Very Good | Free | Yes |

**Recommendation**: Start with **BGE-M3** (free, self-hosted). Upgrade to Voyage if quality issues.

### Best Vector DB

| DB | Hybrid Search | Production Ready | Complexity |
|----|---------------|------------------|------------|
| **Qdrant** | Native (prefetch) | Yes | Medium |
| **Weaviate** | Native (alpha param) | Yes | Medium |
| **ChromaDB** | RRF-based (newer) | Limited | Low |

**Recommendation**: Start with **ChromaDB** for MVP speed. Migrate to Qdrant for production.

### Simplest Architecture That Works

```
1. Chunk documents semantically (300 words, preserve structure)
2. Embed with BGE-M3 (free) or Voyage-3 (quality)
3. Store in ChromaDB (MVP) or Qdrant (production)
4. Retrieve top-50 with hybrid search (BM25 + dense)
5. Fuse with RRF (k=60)
6. Rerank top-15 with Cohere Rerank
7. Send top-5 to Claude with citations prompt
8. Cache everything
```

---

## Key Recommendation: The MVP Stack

### Phase 1: Working Prototype (1 week)

```
┌─────────────────────────────────────────────────────────┐
│                       Frontend                          │
│              Next.js + Vercel AI SDK                    │
│         (streaming chat, citation cards)                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      Backend                            │
│                 FastAPI + Python                        │
│  /search (hybrid) │ /chat (RAG) │ /sources (metadata)  │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   ChromaDB      │ │   Claude API    │ │   Cohere API    │
│   (vectors)     │ │   (synthesis)   │ │   (rerank)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Why this is simpler:**
- ChromaDB: Zero config, pip install, done
- Claude: Best synthesis quality, 200K context
- Cohere Rerank: API call, no infrastructure
- No SPLADE, no ColBERT, no custom models yet

### Phase 2: Production (when needed)

- Migrate ChromaDB → Qdrant
- Add SPLADE sparse embeddings
- Self-host BGE reranker
- Add caching layer (Redis)
- Add evaluation pipeline

---

## What's Missing From Current Plan

### 1. John Cutler Content (CRITICAL)

**Problem**: We have 50 URLs, not actual content.

**Action**: Scrape the posts. Most are on:
- Substack (cutlefish.substack.com) - need to fetch HTML
- Medium (@johnpcutler) - need to fetch HTML

```python
# Need to build: scrape_cutler_posts.py
for url in curated_urls:
    content = fetch_and_extract(url)
    save_as_markdown(content)
```

### 2. Data Format Inconsistency

**Problem**:
- Lenny's uses `guest:` field
- David Senra uses `subject:` field

**Action**: Create unified transformer that normalizes to single schema.

### 3. Book Extraction

**Problem**: 9 books in PDF/EPUB, no extraction pipeline.

**Action**: Build `extract_book.py`:
- EPUB: Use ebooklib (clean text)
- PDF: Use PyMuPDF (preserve structure)
- Chunk by chapter/section, not arbitrary tokens

### 4. No Evaluation Pipeline

**Problem**: No way to measure retrieval or generation quality.

**Action**: Build simple eval:
- 20 test questions with known answers
- Measure retrieval recall@k
- Measure answer correctness
- Run before/after changes

---

## Revised Data Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    SOURCE ADAPTERS                      │
├─────────────────┬─────────────────┬─────────────────────┤
│  Transcripts    │     Books       │     Articles        │
│  (MD + YAML)    │   (EPUB/PDF)    │    (HTML/MD)        │
│                 │                 │                     │
│  - Lenny's      │  - 9 PM books   │  - John Cutler      │
│  - David Senra  │                 │  - (future blogs)   │
│  - Founders     │                 │                     │
└─────────────────┴─────────────────┴─────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Unified Schema        │
              │                         │
              │   {                     │
              │     "id": "uuid",       │
              │     "text": "...",      │
              │     "source_type": "",  │
              │     "source_title": "", │
              │     "author": "",       │
              │     "section": "",      │
              │     "page/timestamp":"",│
              │     "url": ""           │
              │   }                     │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Semantic Chunker      │
              │                         │
              │   - 300-500 words       │
              │   - Preserve sections   │
              │   - Keep speaker turns  │
              │   - Link to parent doc  │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Embed + Index         │
              │                         │
              │   - BGE-M3 (dense)      │
              │   - BM25 (sparse)       │
              │   - Store in ChromaDB   │
              └─────────────────────────┘
```

---

## Immediate Actions

### Today

1. **Scrape John Cutler posts** - Get actual content, not just URLs
2. **Build unified schema transformer** - Normalize Lenny's + David Senra
3. **Test book extraction** - Try one book (Continuous Discovery Habits EPUB)

### This Week

4. **Build ingestion pipeline** - `ingest.py` that handles all sources
5. **Set up ChromaDB** - Index Lenny's + David Senra + Cutler
6. **Build search endpoint** - Basic hybrid search with RRF
7. **Test with 20 queries** - Measure retrieval quality

### Next Week

8. **Add Cohere reranking** - Improve precision
9. **Build chat endpoint** - RAG with citations
10. **Build basic UI** - Streaming chat with citation cards

---

## Model Selection

### For Synthesis (LLM)

| Task | Model | Why |
|------|-------|-----|
| **Answer generation** | Claude 3.5 Sonnet | Best quality, 200K context |
| **Query expansion** | Claude 3.5 Haiku | Fast, cheap |
| **Evaluation** | Claude 3.5 Sonnet | Consistent judging |

### For Embedding

| Start | Upgrade Path |
|-------|--------------|
| BGE-M3 (free, self-host) | Voyage-3-large (if quality issues) |

### For Reranking

| Start | Upgrade Path |
|-------|--------------|
| Cohere Rerank API | Self-host BGE-reranker (if cost issues) |

---

## Success Metrics

### Retrieval Quality
- **Recall@10**: ≥ 80% of relevant docs in top 10
- **Precision@5**: ≥ 60% of top 5 are relevant

### Response Quality
- **Groundedness**: 100% of claims have citations
- **Correctness**: ≥ 85% of answers are accurate
- **Latency**: < 3s to first token

### User Experience
- **Query success rate**: ≥ 90% of queries get useful answers
- **Citation click rate**: Track if users verify sources

---

## Open Questions Resolved

| Question | Decision | Rationale |
|----------|----------|-----------|
| Do we need chunking? | Yes, small-to-big | Corpus is 500+ docs |
| Which vector DB? | ChromaDB → Qdrant | Simple start, clear upgrade |
| Which embedding? | BGE-M3 → Voyage-3 | Free start, quality upgrade |
| Which reranker? | Cohere Rerank API | Best quality, simple integration |
| Which LLM? | Claude 3.5 Sonnet | Best synthesis, long context |
