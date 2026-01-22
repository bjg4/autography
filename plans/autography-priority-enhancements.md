# Plan: Autography Priority Enhancements

## Overview

Priority enhancements for the Autography RAG application to improve retrieval quality, user experience, and prepare for production deployment.

**Current State:**
- 12,486 properly-chunked documents (~500 words each)
- Hybrid search with RRF fusion (70% semantic, 30% BM25)
- Threaded conversations with 3-turn history
- ~4,700 tokens per query (8 sources)
- Working frontend with Next.js + FastAPI backend

## Priority Matrix

| Priority | Category | Enhancement | Impact | Effort |
|----------|----------|-------------|--------|--------|
| P1 | Performance | Fix O(n) doc lookup | High | Small |
| P1 | Performance | Async Anthropic client | High | Small |
| P2 | Retrieval | Add reranking with cross-encoder | High | Medium |
| P2 | UX | Streaming responses in UI | High | Medium |
| P2 | Deployment | Railway + Vercel setup | High | Medium |
| P3 | Retrieval | Better BM25 tokenization | Medium | Small |
| P3 | UX | Source preview expansion | Medium | Small |
| P3 | Performance | Query caching | Medium | Medium |

---

## P1: Critical Performance Fixes

### 1.1 Fix O(n) Document ID Lookup

**Problem:** `api/routers/search.py:171` uses `self.doc_ids.index(doc_id)` which is O(n) for each result.

**Solution:** Build a lookup dict on initialization.

```python
# api/routers/search.py

def _load_bm25(self, bm25_path: str):
    """Load BM25 index from pickle file."""
    with open(bm25_path, 'rb') as f:
        cache = pickle.load(f)
        self.bm25 = cache['bm25']
        self.doc_ids = cache['doc_ids']
        self.doc_texts = cache['doc_texts']
        self.doc_metadatas = cache['doc_metadatas']
        # NEW: Build O(1) lookup
        self.doc_id_to_idx = {doc_id: idx for idx, doc_id in enumerate(self.doc_ids)}
    print(f"Loaded BM25 index ({len(self.doc_ids)} docs)")

# Then in search():
def search(self, ...):
    ...
    for doc_id, score in ranked:
        idx = self.doc_id_to_idx[doc_id]  # O(1) instead of O(n)
        ...
```

**Files:**
- `api/routers/search.py` - Add `doc_id_to_idx` dict, update lookups

### 1.2 Switch to Async Anthropic Client

**Problem:** `api/routers/chat.py:201` uses sync `client.messages.create()` which blocks the FastAPI event loop.

**Solution:** Use `AsyncAnthropic` client.

```python
# api/routers/chat.py

import anthropic
from anthropic import AsyncAnthropic

# Initialize async client
async_client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    ...
    # Use async client
    response = await async_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=messages
    )
    ...
```

**Files:**
- `api/routers/chat.py` - Replace sync client with async

---

## P2: High-Impact Improvements

### 2.1 Add Reranking with Cross-Encoder

**Problem:** Hybrid search returns decent results but could be more relevant. Cross-encoders significantly improve precision.

**Solution:** Add a reranking step with a lightweight cross-encoder.

```python
# api/routers/search.py

from sentence_transformers import CrossEncoder

class HybridSearch:
    def __init__(self, ...):
        ...
        # Load cross-encoder for reranking (89MB model)
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def search(self, query: str, n_results: int = 10, rerank: bool = True, ...):
        # Get more candidates
        n_candidates = n_results * 5
        ...

        if rerank and len(results) > 0:
            # Rerank with cross-encoder
            pairs = [(query, r['content'][:512]) for r in results]
            rerank_scores = self.reranker.predict(pairs)

            # Sort by rerank score
            for i, score in enumerate(rerank_scores):
                results[i]['rerank_score'] = float(score)
            results.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)

        return results[:n_results]
```

**Tradeoff:** Adds ~50-100ms per search but significantly improves relevance.

**Files:**
- `api/routers/search.py` - Add CrossEncoder reranking
- `api/requirements.txt` - Already has sentence-transformers

### 2.2 Streaming Responses in UI

**Problem:** `/api/chat/stream` endpoint exists but frontend doesn't use it. Users wait for full response.

**Solution:** Wire up SSE streaming to the frontend.

```typescript
// web/lib/api.ts

export async function streamChat(
  question: string,
  options: ChatOptions = {},
  onCitation: (citations: Citation[]) => void,
  onToken: (token: string) => void,
  onDone: () => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      n_sources: options.nSources ?? 8,
      source_types: options.sourceTypes,
      authors: options.authors,
      history: options.history,
    }),
  })

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  while (reader) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'citations') onCitation(data.data)
        else if (data.type === 'token') onToken(data.data)
        else if (data.type === 'done') onDone()
      }
    }
  }
}
```

```typescript
// web/app/page.tsx - Update handleSearch

const handleSearch = async () => {
  setLoading(true)
  setStreamingAnswer('')

  await streamChat(
    query,
    { nSources: 8, history: getHistory() },
    (citations) => setCurrentCitations(citations),
    (token) => setStreamingAnswer(prev => prev + token),
    () => {
      // Build final response and add to thread
      setThread(prev => [...prev, {
        question: query,
        response: { answer: streamingAnswer, citations: currentCitations, follow_ups: [] }
      }])
      setLoading(false)
    }
  )
}
```

**Files:**
- `web/lib/api.ts` - Add `streamChat` function
- `web/app/page.tsx` - Use streaming with progressive UI update

### 2.3 Railway + Vercel Deployment

**Architecture:**
```
Vercel (Next.js)  ─────HTTPS────>  Railway (FastAPI)
     │                                    │
     └── Free tier                        └── Hobby ($5-20/mo)
                                               ├── chroma_db/ (192MB)
                                               └── bm25_index.pkl (74MB)
```

**Railway Setup:**

```dockerfile
# api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Download sentence-transformers model on build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# railway.toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"

[[volumes]]
name = "data"
mount = "/app/data"
```

**Vercel Setup:**

```javascript
// web/next.config.js
module.exports = {
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
  },
}
```

**Files:**
- `api/Dockerfile` - Create production container
- `api/railway.toml` - Railway configuration
- `web/next.config.js` - Environment variable for API URL
- `web/.env.production` - Set `API_URL=https://your-railway-app.railway.app`

---

## P3: Nice-to-Have Improvements

### 3.1 Better BM25 Tokenization

**Problem:** Current tokenization is just `.lower().split()` - no stemming or stopword removal.

**Solution:** Use NLTK for better tokenization.

```python
# api/routers/search.py

import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def tokenize(text: str) -> list[str]:
    """Tokenize with stemming and stopword removal."""
    words = nltk.word_tokenize(text.lower())
    return [stemmer.stem(w) for w in words if w.isalnum() and w not in stop_words]
```

**Note:** Requires re-indexing the BM25 corpus with new tokenizer.

**Files:**
- `api/routers/search.py` - Add tokenize function
- `ingestion/index_corpus.py` - Use same tokenizer for indexing
- Re-run: `python ingestion/index_corpus.py --reset`

### 3.2 Source Preview Expansion

**Problem:** Citations show truncated content. Users may want to see full context.

**Solution:** Add expandable source cards with full content.

```typescript
// web/components/SourceCard.tsx

'use client'
import { useState } from 'react'
import { Citation } from '@/lib/api'

export function SourceCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border rounded-lg p-4">
      <div className="flex justify-between items-start">
        <div>
          <span className="text-xs bg-blue-100 px-2 py-1 rounded">
            [{citation.index}]
          </span>
          <h4 className="font-medium mt-1">{citation.title}</h4>
          <p className="text-sm text-gray-500">{citation.author}</p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-blue-600 text-sm"
        >
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      </div>

      <p className="mt-2 text-sm text-gray-700">
        {expanded ? citation.content : citation.content.slice(0, 200) + '...'}
      </p>
    </div>
  )
}
```

**Files:**
- `web/components/SourceCard.tsx` - Create expandable component
- `web/app/page.tsx` - Use SourceCard in thread display

### 3.3 Query Caching

**Problem:** Same questions get asked repeatedly, wasting API tokens.

**Solution:** Add simple in-memory caching with TTL.

```python
# api/routers/chat.py

from functools import lru_cache
from hashlib import md5
import time

# Simple cache with 1-hour TTL
_response_cache: dict[str, tuple[ChatResponse, float]] = {}
CACHE_TTL = 3600  # 1 hour

def get_cached_response(cache_key: str) -> ChatResponse | None:
    if cache_key in _response_cache:
        response, timestamp = _response_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return response
        del _response_cache[cache_key]
    return None

def cache_response(cache_key: str, response: ChatResponse):
    _response_cache[cache_key] = (response, time.time())

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Build cache key (exclude history for base caching)
    cache_key = md5(f"{request.question}:{request.n_sources}".encode()).hexdigest()

    if not request.history:  # Only cache first-turn responses
        cached = get_cached_response(cache_key)
        if cached:
            return cached

    # ... rest of implementation ...

    if not request.history:
        cache_response(cache_key, response)

    return response
```

**Files:**
- `api/routers/chat.py` - Add caching layer

---

## Implementation Order

### Phase 1: Performance (Day 1)
1. Fix O(n) lookup with dict
2. Switch to AsyncAnthropic client

### Phase 2: Quality + Streaming (Day 2-3)
3. Add cross-encoder reranking
4. Implement streaming in frontend

### Phase 3: Deployment (Day 4)
5. Create Dockerfile and railway.toml
6. Configure Vercel with API_URL
7. Deploy and test

### Phase 4: Polish (Day 5+)
8. Better BM25 tokenization (requires re-index)
9. Expandable source cards
10. Query caching

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Search latency | ~300ms | <400ms (with reranking) |
| First token latency | ~2s | <500ms (streaming) |
| Relevance (subjective) | Good | Better (cross-encoder) |
| Production uptime | N/A | 99.5% |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Cross-encoder adds latency | Make reranking optional, cache results |
| Railway costs exceed budget | Monitor usage, implement caching |
| Streaming breaks on errors | Add error boundaries, fallback to non-streaming |
| Re-indexing breaks search | Test locally first, keep backup of bm25_index.pkl |

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `api/routers/search.py` | Modify - Add dict lookup, cross-encoder |
| `api/routers/chat.py` | Modify - Async client, caching |
| `api/Dockerfile` | Create |
| `api/railway.toml` | Create |
| `web/lib/api.ts` | Modify - Add streamChat |
| `web/app/page.tsx` | Modify - Use streaming |
| `web/components/SourceCard.tsx` | Create |
| `web/next.config.js` | Modify - Add API_URL env |
