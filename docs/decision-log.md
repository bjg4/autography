# Autography Decision Log

Architecture and implementation decisions for the PM knowledge base retrieval system.

---

## Decision 001: Everything Becomes Markdown

**Date:** 2026-01-19
**Status:** Approved
**Context:** We have content from multiple sources (blog posts, podcast transcripts, books) in various formats.

### Decision

All content will be normalized to markdown files with YAML frontmatter. This includes:
- Blog posts (already markdown) ✓
- Podcast transcripts (already markdown) ✓
- Books (PDF/EPUB → extract to markdown chapters)

### Rationale

1. **Single source of truth**: Markdown files are human-readable and version-controllable
2. **No vendor lock-in**: Can switch vector DBs without re-processing source content
3. **Debuggable**: Can inspect exactly what's being indexed
4. **Consistent metadata**: YAML frontmatter provides uniform structure across all sources
5. **Claude-friendly**: Markdown renders well in Claude's context window

### Structure

```
/data
  /blake-green/posts/*.md       # Blog essays
  /john-cutler/posts/*.md       # Substack/Medium posts
  /lennys/episodes/*.md         # Podcast transcripts
  /david-senra/episodes/*.md    # Podcast transcripts
  /books/
    /extracted/                 # NEW: Book chapters as markdown
      /shape-up/
        ch01-introduction.md
        ch02-principles.md
        ...
      /inspired/
        ch01-what-is-product.md
        ...
```

---

## Decision 002: Chunking Strategy - Full Docs vs Chapters

**Date:** 2026-01-19
**Status:** Approved
**Context:** Traditional RAG systems chunk documents into 500-800 token pieces. Modern long-context models (200k tokens) may not need this.

### Decision

**Hybrid approach based on content type:**

| Content Type | Strategy | Rationale |
|--------------|----------|-----------|
| Blog posts (1-5k words) | Full document | Fits easily in context, preserves complete arguments |
| Podcast transcripts | Full document* | Test first; section if >50k tokens |
| Book chapters | Chapter-level | Natural boundaries, independent ideas |

### Rationale

1. **Cursor's insight**: Semantic search helps most on large codebases. Our 365-doc corpus is small.
2. **Anthropic's finding**: Chunking loses context. Full docs preserve it.
3. **Books are different**: A 300-page book can't fit in one retrieval. Chapters are natural semantic units.
4. **Test-driven**: Start simple (full docs), add chunking only if retrieval quality suffers.

### Anti-pattern avoided

Traditional 500-token chunking would:
- Fragment Cutler's arguments mid-thought
- Lose "this refers to..." context
- Require contextual embedding for every chunk (cost + complexity)

---

## Decision 003: Hybrid Search (Semantic + BM25)

**Date:** 2026-01-19
**Status:** Approved
**Context:** Pure semantic search can miss exact terms; pure keyword search misses meaning.

### Decision

Implement hybrid search with **70% semantic / 30% BM25** weighting.

### Evidence

| Source | Finding |
|--------|---------|
| Cursor | Semantic search adds 12.5% accuracy, especially on large codebases |
| Anthropic | BM25 + embeddings = 49% reduction in retrieval failures |
| Chroma docs | Hybrid "captures both meaning and exact keywords" |

### Implementation

```python
# Reciprocal Rank Fusion (RRF) combining both signals
hybrid_score = (0.7 * semantic_score) + (0.3 * bm25_score)
```

### Query type mapping

| Query | Primary Signal |
|-------|---------------|
| "What is a feature factory?" | Semantic (concept) |
| "Cutler NPS article" | BM25 (exact terms) + metadata filter |
| "How to write one-pagers" | Hybrid (concept + term) |

---

## Decision 004: Embedding Model Selection

**Date:** 2026-01-19
**Status:** Approved
**Context:** Multiple embedding options available with different cost/quality tradeoffs.

### Decision

Start with **BGE-M3** (free, local), upgrade to **Voyage-3** if quality insufficient.

### Comparison

| Model | MTEB Score | Cost | Notes |
|-------|------------|------|-------|
| Voyage-3-large | 63.8 | $0.12/1M tokens | Best quality |
| text-embedding-3-large | 64.6 | $0.13/1M tokens | OpenAI ecosystem |
| **BGE-M3** | 63.0 | **Free** | Built-in hybrid support |
| nomic-embed-text-v2 | ~62 | Free | Good open source option |

### Rationale

1. **BGE-M3 uniquely supports** dense + sparse embeddings in one model (hybrid search native)
2. **Cost for 365 docs**: Negligible either way (~$0.25 for Voyage)
3. **Local-first**: BGE-M3 runs on Mac, no API dependency
4. **Upgrade path**: If BGE-M3 underperforms, switch to Voyage-3 is simple

---

## Decision 005: Skip Contextual Embedding (For Now)

**Date:** 2026-01-19
**Status:** Approved
**Context:** Anthropic's contextual retrieval prepends context to chunks before embedding, reducing failures by 35-67%.

### Decision

**Skip contextual embedding initially** because we're not chunking most content.

### Rationale

1. Contextual embedding solves the problem of **chunks losing context**
2. We're using **full documents** for posts/transcripts—context is preserved
3. For **book chapters**, the chapter title + book title in frontmatter provides context
4. Adding contextual embedding later is easy if needed

### When to reconsider

- If retrieval quality is poor on book chapters
- If we need finer-grained (sub-chapter) retrieval
- If Lenny's transcripts need sectioning

---

## Decision 006: PDF Extraction Tool

**Date:** 2026-01-19
**Status:** Approved
**Context:** Need to extract PM books (PDF/EPUB) to markdown with chapter structure.

### Decision

Use **pymupdf4llm** with custom TOC-based chapter splitting.

### Comparison

| Tool | Speed | Structure | Best For |
|------|-------|-----------|----------|
| marker-pdf | 11-12s | Excellent | Books with chapters (requires Python 3.10+) |
| **pymupdf4llm** | 0.12s | Very Good | General docs, Python 3.9 compatible |
| Docling | Slower | Excellent | Complex layouts |

### Rationale

1. **marker-pdf** requires Python 3.10+ (surya-ocr dependency uses `Type | None` syntax)
2. **pymupdf4llm** is Python 3.9 compatible and fast (~0.12s per book)
3. Custom `extract_book.py` script adds TOC-based chapter splitting
4. Results are readable with valid frontmatter; PDF artifacts (page headers) are acceptable

### Implementation

```python
# ingestion/extract_book.py - TOC-based chapter extraction
import pymupdf4llm
import pymupdf

doc = pymupdf.open(pdf_path)
chapters = doc.get_toc()  # Extract table of contents
md_text = pymupdf4llm.to_markdown(pdf_path)
# Split by chapter headers, add YAML frontmatter
```

### Validation (Shape Up)

- Extracted: 40 chapters + full-book.md
- Total: 191,651 characters of markdown
- Frontmatter: Valid YAML with title, author, book_title, chapter_number
- Content: Readable, headers preserved, some PDF page artifacts present

---

## Decision 007: Vector Database Choice

**Date:** 2026-01-19
**Status:** Approved
**Context:** Need to store embeddings and enable hybrid search.

### Decision

Use **Chroma** with `PersistentClient` for MVP.

### Rationale

1. **Already in .gitignore**: Project anticipated Chroma (`chroma_db/` excluded)
2. **No server needed**: `PersistentClient` stores locally
3. **Native hybrid search**: Supports RRF out of the box
4. **Simple Python API**: Minimal boilerplate
5. **Migration path**: Can move to Qdrant/Pinecone later if needed

### Configuration

```python
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="autography",
    metadata={"hnsw:space": "cosine"}
)
```

---

## Decision 008: Metadata Schema

**Date:** 2026-01-19
**Status:** Approved
**Context:** Need consistent metadata for filtering and attribution.

### Decision

Standardize on this YAML frontmatter schema:

```yaml
---
title: "Chapter/Post Title"
author: "Author Name"
source_url: "https://..."
source_type: "book_chapter | essay | podcast_transcript"
publish_date: "2025-12-27"
scraped_date: "2026-01-19"

# Book-specific (optional)
book_title: "Inspired"
chapter_number: 14
chapter_title: "Product Vision and Strategy"

# Podcast-specific (optional)
guest: "Guest Name"
duration: "1:54:40"
---
```

### Rationale

1. **Enables filtering**: `source_type == "book_chapter"`
2. **Attribution**: Always know where content came from
3. **Temporal queries**: "What did authors say about X in 2024?"
4. **Consistent across sources**: Same schema for all content types

---

## Future Decisions (Not Yet Made)

- [ ] Reranking: Add Cohere or cross-encoder reranker?
- [ ] Agentic search: Implement multi-step retrieval for complex queries?
- [ ] Frontend: Next.js + Vercel AI SDK vs simpler CLI?
- [ ] Caching: Cache frequent queries?

---

## Pending: Next Re-Index

Tasks to complete during the next corpus re-indexing:

- [ ] **Fix author name**: blake.ist posts show "Blake Green" but should be "Blake Graham" (code fixed in `ingestion/index_corpus.py`, needs re-index to update ChromaDB)

*Bundle with adding new sources to minimize re-indexing overhead.*

---

*Last updated: 2026-01-22*
