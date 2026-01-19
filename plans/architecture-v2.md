# Autography: Architecture for the Best PM Knowledge Base

> Goal: Beat OpenEvidence. Fast, citable, multi-perspective, expandable.

## What Makes OpenEvidence Great (and How to Beat It)

OpenEvidence works because:
1. **Speed** - Sub-second responses
2. **Citations** - Every claim linked to source
3. **Trust** - Medical literature is authoritative
4. **Specificity** - Answers long-tail questions others can't

We beat it by:
1. **Richer sources** - Not just papers, but founder stories, practitioner wisdom, real examples
2. **Multiple perspectives** - "Here's what Marty Cagan says... but Ben Horowitz disagrees..."
3. **Temporal context** - "In 2016, this was best practice. By 2024, thinking evolved..."
4. **Practitioner-first** - Written for PMs who need answers NOW, not researchers

---

## Core Requirements

### 1. FAST (< 500ms to first token)

**Strategy:**
- Pre-computed embeddings at ingestion time
- HNSW index for approximate nearest neighbor (not brute force)
- Streaming responses (don't wait for full answer)
- Edge caching for common queries
- Hybrid retrieval in parallel (not sequential)

**Tech choices:**
- **Vector DB**: Qdrant or Weaviate (faster than ChromaDB for production)
- **Embeddings**: Cohere embed-v3 or Voyage-3 (better than OpenAI for retrieval)
- **LLM**: Claude 3.5 Sonnet for synthesis (fast + smart)
- **Hosting**: Fly.io or Modal (edge deployment)

### 2. CITATIONS (Every claim traceable)

**Strategy:**
- Chunk-level metadata: source, page/timestamp, speaker, date
- Return top-k chunks with relevance scores
- LLM outputs inline citations: [1], [2], [3]
- Expandable citation cards in UI

**Chunk schema:**
```json
{
  "id": "uuid",
  "text": "The actual content...",
  "source_type": "podcast|book|article",
  "source_title": "Inspired",
  "source_author": "Marty Cagan",
  "chapter": "Chapter 5: Product Vision",
  "page": 47,
  "timestamp": "00:23:45",
  "speaker": "Marty Cagan",
  "publish_date": "2018-01-01",
  "url": "https://...",
  "embedding": [0.1, 0.2, ...]
}
```

### 3. MULTIPLE PERSPECTIVES

**Strategy:**
- Retrieve from diverse sources (not just top-k from one)
- Source diversity in retrieval: max 3 chunks per source
- Prompt engineering: "Present multiple viewpoints if experts disagree"
- Tag contradictions explicitly

**Example output:**
> **On whether PMs should code:**
>
> Marty Cagan (Inspired) argues PMs should understand technology deeply: "You can't effectively work with engineers if you don't understand their constraints." [1]
>
> However, Ben Horowitz (Hard Thing) cautions: "The best PMs I've worked with weren't the most technical—they were the best at understanding customers." [2]
>
> Teresa Torres (Continuous Discovery) offers a middle ground: "Technical literacy matters, but customer empathy matters more." [3]

### 4. HYBRID SEARCH (Lexical + Semantic)

**Why hybrid beats pure semantic:**
- Semantic: Great for conceptual questions ("how do I prioritize?")
- Lexical: Great for specific terms ("OKR", "North Star metric", "RICE framework")
- Hybrid: Best of both, catches edge cases

**Implementation:**
```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└─────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌─────────────────┐       ┌─────────────────┐
    │  Sparse Search  │       │  Dense Search   │
    │  (BM25/SPLADE)  │       │  (Embeddings)   │
    └─────────────────┘       └─────────────────┘
              │                         │
              └────────────┬────────────┘
                           ▼
              ┌─────────────────────────┐
              │   Reciprocal Rank       │
              │   Fusion (RRF)          │
              │   k=60, α=0.7 dense     │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Cross-Encoder         │
              │   Reranking             │
              │   (bge-reranker-v2-m3)  │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Top 10 chunks         │
              │   + metadata            │
              └─────────────────────────┘
```

**Tech choices:**
- **Sparse**: SPLADE or BM25 (Qdrant supports both)
- **Dense**: Voyage-3 or Cohere embed-v3
- **Fusion**: RRF with k=60
- **Reranker**: Cohere rerank-v3 or bge-reranker-v2-m3

### 5. EXPANDABLE OVER TIME

**Modular ingestion pipeline:**
```
┌─────────────────────────────────────────────────────────┐
│                   Source Adapters                       │
├─────────────┬─────────────┬─────────────┬──────────────┤
│  Podcast    │   Book      │   Article   │   Custom     │
│  (MD+YAML)  │  (EPUB/PDF) │   (HTML)    │   (API)      │
└─────────────┴─────────────┴─────────────┴──────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Unified Chunker       │
              │   - 512 tokens          │
              │   - 100 token overlap   │
              │   - Semantic boundaries │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Metadata Enrichment   │
              │   - Entity extraction   │
              │   - Topic classification│
              │   - Quality scoring     │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Embedding + Indexing  │
              │   - Batch embed         │
              │   - Upsert to vector DB │
              │   - Sparse index update │
              └─────────────────────────┘
```

**Adding new sources:**
1. Write adapter (parse format → unified chunks)
2. Run through pipeline
3. Automatic index update
4. No code changes to search/synthesis

### 6. COMPREHENSIVE COVERAGE

**Current corpus:**
| Source | Count | Hours/Pages | Status |
|--------|-------|-------------|--------|
| Lenny's Podcast | 269 eps | ~400 hrs | Ready |
| David Senra | 9 eps | ~14 hrs | Transcribed |
| Founders Podcast | 100 eps | ~150 hrs | Pending |
| John Cutler | 50 posts | ~200 pages | Curated |
| PM Books | 9 books | ~2000 pages | Added |

**Total at launch:** ~500 sources, ~600 hours audio, ~2500 pages text

**Expansion roadmap:**
- Phase 2: First Round Review, a]16z blog, Stratechery
- Phase 3: Conference talks (MTP, ProductCon)
- Phase 4: User-submitted sources (with curation)

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│                    Next.js 15 + Vercel                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Search Bar  │  │ Chat UI     │  │ Citation Cards          │ │
│  │ (instant)   │  │ (streaming) │  │ (expandable, linkable)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Vercel AI SDK (streaming)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                              │
│                     FastAPI + Python                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ /search     │  │ /chat       │  │ /sources                │ │
│  │ (hybrid)    │  │ (RAG)       │  │ (metadata)              │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Qdrant        │ │   Claude API    │ │   Cohere API    │
│   (vectors +    │ │   (synthesis)   │ │   (embed +      │
│    sparse)      │ │                 │ │    rerank)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Query Flow (Detailed)

```
User: "How should I handle a PM who keeps missing deadlines?"

1. QUERY UNDERSTANDING (50ms)
   - Classify: management question
   - Extract entities: PM, deadlines, performance
   - Expand: "accountability", "1:1s", "expectations"

2. HYBRID RETRIEVAL (100ms, parallel)
   - Dense search: top 50 by embedding similarity
   - Sparse search: top 50 by BM25 on expanded query
   - RRF fusion: merge with k=60

3. RERANKING (150ms)
   - Cross-encoder scores top 100 → top 15
   - Diversity filter: max 3 per source

4. SYNTHESIS (streaming, 500ms to first token)
   - Context: 15 chunks + metadata
   - Prompt: "Answer with citations, present multiple views"
   - Stream response with [1], [2], [3] inline

5. RESPONSE
   - Streamed answer with inline citations
   - Citation cards with source details
   - "Related questions" suggestions
```

---

## Differentiators vs. ChatGPT/Perplexity

| Feature | ChatGPT | Perplexity | Autography |
|---------|---------|------------|------------|
| PM-specific corpus | ❌ General | ❌ Web search | ✅ Curated PM content |
| Timestamp citations | ❌ | ❌ | ✅ Jump to exact moment |
| Multiple perspectives | ❌ | Partial | ✅ Explicit disagreements |
| Practitioner voices | ❌ | ❌ | ✅ Real founder stories |
| Offline/curated | ❌ | ❌ | ✅ No SEO spam |

---

## MVP Scope (v0.1)

**In scope:**
- [ ] Hybrid search API (Qdrant + BM25)
- [ ] Basic RAG with citations
- [ ] Streaming chat UI
- [ ] Citation cards with source links
- [ ] Lenny's + David Senra + Books indexed

**Out of scope (v0.2+):**
- User accounts / saved searches
- Follow-up question generation
- Source quality scoring
- User-submitted content

---

## Open Questions

1. **Hosting**: Vercel + Railway? Or all on Fly.io?
2. **Embedding model**: Voyage-3 ($) vs. BGE-m3 (free, self-host)?
3. **Vector DB**: Qdrant Cloud vs. self-hosted?
4. **Books**: Full text or chapter summaries? (Copyright concern)
5. **Pricing**: Free tier? Usage limits?

---

## Next Actions

1. [ ] Set up Qdrant (cloud or local)
2. [ ] Build ingestion pipeline for transcripts
3. [ ] Build ingestion pipeline for books (EPUB → chunks)
4. [ ] Create hybrid search endpoint
5. [ ] Build basic chat UI with streaming
6. [ ] Index Lenny's + David Senra + Books
7. [ ] Test with 20 sample queries
8. [ ] Iterate on retrieval quality
