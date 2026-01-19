# Autography: Product Management Knowledge Graph

> "The open evidence of product management"

A searchable, citable knowledge base synthesizing the best thinking in product management, entrepreneurship, and design from newsletters, podcasts, and canonical books.

---

## Vision

Users ask long-tail questions like:
- "How should I structure my product pod?"
- "What are the different frameworks for prioritization?"
- "How did successful founders handle their first 10 hires?"

Autography returns **citable evidence** from curated sources, with attributions, context, and the ability to dig deeper.

---

## Data Corpus

### Primary Sources

| Source | Type | Content | Est. Volume |
|--------|------|---------|-------------|
| **Lenny's Newsletter** | Newsletter/Podcast | Product management insights, interviews, frameworks | ~500+ articles, ~200 podcast episodes |
| **Founders Podcast** (David Senra) | Podcast | Biographies of founders, distilled wisdom | ~350+ episodes |
| **David Senra's New Podcast** | Podcast | TBD - newer content | ~50+ episodes |
| **John Cutler** | Blog/Newsletter | Team topology, product ops, organizational design | ~1000+ posts |

### Canonical Books (Top 20)

1. *The Design of Everyday Things* - Don Norman
2. *The Hard Thing About Hard Things* - Ben Horowitz
3. *The Making of a Manager* - Julie Zhuo
4. *Team Topologies* - Matthew Skelton & Manuel Pais
5. *Don't Make Me Think* - Steve Krug
6. *Inspired* - Marty Cagan
7. *Continuous Discovery Habits* - Teresa Torres
8. *Escaping the Build Trap* - Melissa Perri
9. *The Lean Startup* - Eric Ries
10. *Zero to One* - Peter Thiel
11. *Good Strategy Bad Strategy* - Richard Rumelt
12. *Thinking in Bets* - Annie Duke
13. *The Mom Test* - Rob Fitzpatrick
14. *Hooked* - Nir Eyal
15. *Measure What Matters* - John Doerr
16. *High Output Management* - Andy Grove
17. *The Innovator's Dilemma* - Clayton Christensen
18. *Crossing the Chasm* - Geoffrey Moore
19. *Atomic Habits* - James Clear
20. *Shape Up* - Ryan Singer (Basecamp)

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Warm, modern chat interface                            │   │
│  │  - Search box (primary)                                 │   │
│  │  - Suggestion cards ("Surprise me", "Explore topics")   │   │
│  │  - Citation previews with source attribution            │   │
│  │  - User memory / personalization sidebar                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENTIC LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Query        │  │ Multi-hop    │  │ Synthesis &           │ │
│  │ Understanding│─▶│ Retrieval    │─▶│ Citation Generation   │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
│         │                                       │               │
│         ▼                                       ▼               │
│  ┌──────────────┐                    ┌───────────────────────┐ │
│  │ Query        │                    │ Follow-up Question    │ │
│  │ Expansion    │                    │ Generation            │ │
│  └──────────────┘                    └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL LAYER                              │
│  ┌────────────────────────────────────────────────────────────┐│
│  │              HYBRID SEARCH                                 ││
│  │  ┌─────────────────┐    ┌─────────────────┐               ││
│  │  │ Semantic Search │ +  │ BM25 Keyword    │  → Re-ranking ││
│  │  │ (Embeddings)    │    │ Search          │               ││
│  │  └─────────────────┘    └─────────────────┘               ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   ChromaDB                              │   │
│  │  - Vector embeddings (semantic search)                  │   │
│  │  - Full-text search (BM25)                              │   │
│  │  - Metadata filtering (source, author, topic, date)     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   SQLite/Postgres                       │   │
│  │  - User profiles & preferences                          │   │
│  │  - Search history & bookmarks                           │   │
│  │  - Citation metadata & source links                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DATA INGESTION PIPELINE                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Scrapers &  │─▶│ Chunking &  │─▶│ Embedding Generation    │ │
│  │ Extractors  │  │ Processing  │  │ (OpenAI/Anthropic)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Ingestion Pipeline

### 1.1 Content Acquisition Strategy

**Lenny's Newsletter**
- Substack API or RSS feed scraping
- Podcast episode transcripts (YouTube auto-transcripts or paid transcription)
- Archive of all articles with metadata

**Founders Podcast**
- Transcript extraction from YouTube (whisper or paid service)
- Episode metadata from podcast feed
- Book references and timestamps

**John Cutler**
- Medium archive scraping
- Twitter/X thread compilation
- Amplitude blog posts

**Books**
- Legal consideration: Use summaries, key quotes, and fair-use excerpts
- Partner with publishers or use existing summary services
- Manual curation of key passages with proper attribution

### 1.2 Chunking Strategy

```python
# Semantic chunking approach
CHUNK_CONFIG = {
    "target_size": 512,        # tokens
    "overlap": 64,             # tokens
    "respect_boundaries": True, # paragraphs, sections
    "metadata_enrichment": {
        "source": str,         # "founders_podcast", "lenny", etc.
        "author": str,         # attribution
        "episode_or_chapter": str,
        "timestamp_or_page": str,
        "topic_tags": list,    # auto-generated
        "date_published": date,
        "url_or_reference": str,
    }
}
```

### 1.3 Embedding Model Selection

| Option | Pros | Cons |
|--------|------|------|
| OpenAI `text-embedding-3-large` | High quality, 3072 dims | Cost at scale |
| Voyage AI `voyage-3` | Great for retrieval | Newer, less battle-tested |
| Cohere `embed-v3` | Multi-lingual, re-ranker bundle | API dependency |
| Local: `nomic-embed-text` | Free, privacy | Lower quality |

**Recommendation**: Start with OpenAI `text-embedding-3-small` (1536 dims) for cost efficiency, upgrade later.

---

## Phase 2: Storage & Retrieval

### 2.1 ChromaDB Setup

```python
import chromadb
from chromadb.config import Settings

# Persistent storage
client = chromadb.PersistentClient(
    path="./autography_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Collection with metadata
collection = client.create_collection(
    name="autography_corpus",
    metadata={"hnsw:space": "cosine"},
    embedding_function=openai_embedding_function
)
```

### 2.2 Hybrid Search Implementation

```python
def hybrid_search(query: str, top_k: int = 20, rerank_top: int = 5):
    """
    Combines semantic + keyword search with re-ranking
    """
    # 1. Semantic search via embeddings
    semantic_results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # 2. BM25 keyword search (Chroma's built-in or separate)
    keyword_results = bm25_search(query, top_k)

    # 3. Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion(semantic_results, keyword_results)

    # 4. Re-rank with cross-encoder (optional, high quality)
    reranked = cross_encoder_rerank(query, fused[:rerank_top])

    return reranked
```

### 2.3 Metadata Filtering

Support queries like:
- "What does David Senra say about hiring?" → filter by source
- "Recent thinking on prioritization" → filter by date
- "Frameworks from books" → filter by content type

---

## Phase 3: Agentic Processing Layer

### 3.1 Query Understanding Agent

```python
QUERY_UNDERSTANDING_PROMPT = """
Analyze the user's question and determine:
1. Primary intent (explore, compare, find examples, get framework)
2. Key concepts to search for
3. Relevant sources to prioritize
4. Whether multi-hop retrieval is needed

User question: {query}
"""
```

### 3.2 Multi-hop Retrieval

For complex questions like "How do the best founders handle disagreement with their co-founders?":

1. **First hop**: Find content about founder relationships
2. **Second hop**: Find specific conflict resolution examples
3. **Third hop**: Find frameworks for handling disagreement
4. **Synthesize**: Combine with proper citations

### 3.3 Citation Generation

Every response must include:
```markdown
**Finding**: Teams of 5-8 work best for autonomous product pods.

> "The ideal team size is between 5-8 people. Larger than that and communication overhead kills velocity."
> — Marty Cagan, *Inspired*, Chapter 12

> "Two-pizza teams aren't just about food—they're about cognitive load."
> — Lenny's Newsletter, "How to Structure Product Teams" (2024)
```

---

## Phase 4: Frontend Design

### 4.1 Design Principles

- **Warm & Inviting**: Cream backgrounds, soft shadows, readable typography
- **Search-First**: Large, centered search box as hero
- **Evidence-Forward**: Citations prominent, not hidden
- **Dig Deeper**: Every result invites exploration

### 4.2 Core Components

```
┌────────────────────────────────────────────────────────────────┐
│  🔤 AUTOGRAPHY                               [Memory] [About]  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│     ╭────────────────────────────────────────────────────╮    │
│     │  🔍 Ask anything about product, founders, design...│    │
│     ╰────────────────────────────────────────────────────╯    │
│                                                                │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│     │ 🎲 Surprise  │  │ 📚 Browse    │  │ 🔥 Trending  │     │
│     │    Me        │  │    Sources   │  │    Questions │     │
│     └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│  RECENT EXPLORATIONS                                           │
│  ├─ "How to prioritize ruthlessly" · 3 sources cited          │
│  ├─ "First 90 days as PM" · 7 sources cited                   │
│  └─ "When to pivot" · 5 sources cited                         │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Results View

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back    "How should I structure my product pod?"            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  SYNTHESIS                                                     │
│  ──────────────────────────────────────────────────────────   │
│  The optimal product pod structure depends on your stage      │
│  and complexity. Here's what the evidence suggests...         │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 📖 CITATION 1                                    [Open]│   │
│  │ "Keep pods to 5-8 people. Include: PM, designer,      │   │
│  │  2-4 engineers, and half a data analyst."             │   │
│  │                                                        │   │
│  │ — Marty Cagan, Inspired (Chapter 12)                  │   │
│  │ #team-structure #pod-design                           │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 📖 CITATION 2                                    [Open]│   │
│  │ "Stream-aligned teams should be long-lived and        │   │
│  │  funded as a product, not a project."                 │   │
│  │                                                        │   │
│  │ — Team Topologies, Skelton & Pais (p. 89)             │   │
│  │ #team-topologies #org-design                          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  FOLLOW-UP QUESTIONS                                          │
│  ├─ "How do pods handle dependencies?"                        │
│  ├─ "What roles are optional in early-stage?"                 │
│  └─ "How did Stripe structure their pods?"                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 4.4 Tech Stack for Frontend

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | Next.js 15 | React Server Components, great DX |
| Styling | Tailwind + shadcn/ui | Rapid iteration, consistent design |
| State | Zustand | Simple, lightweight |
| Search UX | cmdk | Command palette feel |
| Animations | Framer Motion | Polished micro-interactions |

---

## Phase 5: Personalization & Memory

### 5.1 User Memory Schema

```typescript
interface UserProfile {
  id: string;
  searchHistory: SearchEntry[];
  bookmarkedCitations: Citation[];
  topicAffinities: TopicScore[];  // learned from behavior
  preferredSources: string[];     // explicit preference
  recentQuestions: string[];
}

interface SearchEntry {
  query: string;
  timestamp: Date;
  citationsViewed: string[];
  dwellTime: number;  // engagement signal
}
```

### 5.2 Personalization Features

1. **"Your Topics"**: Surface content related to past interests
2. **Source Preferences**: Weight results by preferred authors
3. **Continuation**: "Last time you asked about X, want to go deeper?"
4. **Smart Suggestions**: Based on similar users' journeys

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up project structure (Next.js + Python backend)
- [ ] Initialize ChromaDB with test data
- [ ] Build basic ingestion pipeline for 1 source (Founders Podcast)
- [ ] Implement simple semantic search

### Phase 2: Core Search (Week 3-4)
- [ ] Add remaining data sources (Lenny, Cutler)
- [ ] Implement hybrid search with BM25
- [ ] Build citation extraction and formatting
- [ ] Create basic API endpoints

### Phase 3: Agentic Layer (Week 5-6)
- [ ] Query understanding agent
- [ ] Multi-hop retrieval for complex queries
- [ ] Synthesis with citations
- [ ] Follow-up question generation

### Phase 4: Frontend (Week 7-8)
- [ ] Design system and components
- [ ] Search interface
- [ ] Results view with citations
- [ ] Source browsing

### Phase 5: Personalization (Week 9-10)
- [ ] User accounts and memory
- [ ] Search history
- [ ] Recommendations
- [ ] "Surprise me" feature

### Phase 6: Polish & Scale (Week 11-12)
- [ ] Performance optimization
- [ ] Add book content
- [ ] Testing and refinement
- [ ] Deploy

---

## Open Questions

1. **Legal**: How to handle book content? Fair use excerpts vs. summaries vs. partnerships?
2. **Transcripts**: Pay for professional transcription or use Whisper?
3. **Hosting**: Vercel + managed DB vs. self-hosted for cost at scale?
4. **Auth**: Open access vs. freemium vs. paid?
5. **Updates**: How to handle new content (newsletters, episodes)?

---

## Alternative Considerations

### Instead of Chroma

| Option | Consideration |
|--------|---------------|
| **Pinecone** | Managed, scales well, but costs add up |
| **Weaviate** | Great hybrid search built-in, self-hostable |
| **Qdrant** | Fast, Rust-based, good for scale |
| **Postgres + pgvector** | All-in-one if you need relational data anyway |

**Recommendation**: Start with Chroma for simplicity, migrate to Qdrant or pgvector if scaling becomes an issue.

### RAG Improvements

- **ColBERT**: Token-level matching for better retrieval
- **HyDE**: Hypothetical document embeddings for query expansion
- **RAPTOR**: Recursive summarization for hierarchical retrieval

---

## Success Metrics

1. **Retrieval Quality**: % of relevant citations in top 5
2. **User Satisfaction**: Would users recommend to colleagues?
3. **Engagement**: Return visits, queries per session
4. **Citation Click-through**: Do users find citations valuable?

---

## Next Steps

1. Validate data acquisition strategy (can we get the content?)
2. Build a minimal prototype with 50 documents
3. Test search quality with real PM questions
4. Design high-fidelity mockups
5. Decide on hosting and auth strategy

---

*"The best product managers are T-shaped: deep in one area, broad across many. Autography helps you go deep and broad simultaneously."*
