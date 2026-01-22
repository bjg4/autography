# RAG UI with Citations (OpenEvidence-Style)

---
title: RAG UI with Citations
category: feature-implementations
tags: [rag, nextjs, fastapi, claude-api, hybrid-search, citations]
created: 2026-01-20
status: completed
components: [web/, api/]
---

## Problem Statement

Build a search UI for the Autography PM knowledge base that synthesizes answers from 696 documents across 12 authors. The initial implementation returned raw search chunks, but the goal was an **OpenEvidence-style experience**: synthesized answers with inline citations, hover previews, source diversity, and progress feedback.

**Key constraint**: Vercel serverless functions have a 250MB limit. ChromaDB (192MB) + BM25 index (44MB) + SentenceTransformers exceeds this.

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel (Next.js 15)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │  Search UI  │  │  Progress   │  │  Citation Cards  │    │
│  └─────────────┘  └─────────────┘  └──────────────────┘    │
│              ┌──────────▼──────────┐                       │
│              │  next.config.js     │  (rewrites to backend)│
│              └──────────┬──────────┘                       │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              /api/chat (RAG endpoint)                │   │
│  │  1. Hybrid search (semantic + BM25)                  │   │
│  │  2. Source diversity filtering                       │   │
│  │  3. Claude API synthesis with citations              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Implementation Details

### 1. RAG Pipeline (`api/routers/chat.py`)

```python
SYSTEM_PROMPT = """You are Autography, a warm and knowledgeable assistant...

IMPORTANT RULES:
1. ALWAYS cite your sources using [1], [2], [3] notation
2. Only use information from the provided sources - never make things up
3. If the sources don't contain relevant information, say so honestly
4. End with "Follow-up questions:" section"""

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # 1. Hybrid search with diversity
    engine = get_search_engine()
    results = engine.search(
        query=request.question,
        n_results=request.n_sources,
        mode="hybrid"
    )

    # 2. Format sources for Claude context
    context, citations = format_sources_for_context(results)

    # 3. Claude synthesizes answer with citations
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    # 4. Extract follow-up questions
    clean_answer, follow_ups = extract_follow_ups(response.content[0].text)

    return ChatResponse(answer=clean_answer, citations=citations, follow_ups=follow_ups)
```

### 2. Source Diversity (`api/routers/search.py`)

```python
def search(self, query, n_results=10, diversify=True):
    n_candidates = n_results * 5  # Over-fetch for diversity

    # Track seen authors/sources
    seen_authors = {}
    seen_sources = {}

    for doc_id, score in ranked:
        if diversify:
            # Max 3 results per author
            if seen_authors.get(doc_author, 0) >= 3:
                continue
            # Max 2 results per source title
            if seen_sources.get(doc_source, 0) >= 2:
                continue

            seen_authors[doc_author] = seen_authors.get(doc_author, 0) + 1
            seen_sources[doc_source] = seen_sources.get(doc_source, 0) + 1

        results.append({...})
```

### 3. Citation Hover Previews with React Portal (`web/components/AnswerDisplay.tsx`)

```tsx
function CitationBadge({ index, citation, onClick }) {
  const [mounted, setMounted] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  // Avoid hydration errors - only render portal after mount
  useEffect(() => { setMounted(true) }, [])

  const handleMouseEnter = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setPosition({
      top: rect.top + window.scrollY - 8,
      left: rect.left + rect.width / 2
    })
    setShowPreview(true)
  }

  return (
    <>
      <button onMouseEnter={handleMouseEnter} onMouseLeave={() => setShowPreview(false)}>
        {index}
      </button>
      {mounted && showPreview && citation && createPortal(
        <div
          className="fixed w-72 p-3 bg-white rounded-lg shadow-xl"
          style={{ top: position.top, left: position.left, transform: 'translate(-50%, -100%)' }}
        >
          <div className="font-medium text-sm">{citation.title}</div>
          <div className="text-xs text-gray-500">{citation.author}</div>
          <p className="text-xs mt-2 line-clamp-3">{citation.content.slice(0, 200)}...</p>
        </div>,
        document.body
      )}
    </>
  )
}
```

### 4. Progress Indicator (`web/app/page.tsx`)

```tsx
const PROGRESS_STEPS = [
  { message: 'Understanding your question...', duration: 800 },
  { message: 'Searching across sources...', duration: 1500 },
  { message: 'Finding relevant passages...', duration: 1200 },
  { message: 'Ranking by relevance...', duration: 1000 },
  { message: 'Synthesizing answer with AI...', duration: 3000 },
]

// Advance through steps during loading
useEffect(() => {
  if (!isLoading) return

  let step = 0
  const advanceStep = () => {
    if (step < PROGRESS_STEPS.length - 1) {
      step++
      setProgressStep(step)
      setTimeout(advanceStep, PROGRESS_STEPS[step].duration)
    }
  }
  setTimeout(advanceStep, PROGRESS_STEPS[0].duration)
}, [isLoading])
```

### 5. API Proxy (`web/next.config.js`)

```javascript
async rewrites() {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
  return [
    { source: '/api/:path*', destination: `${backendUrl}/api/:path*` }
  ]
}
```

## Issues Encountered & Solutions

### 1. React Hydration Error (`<div>` inside `<p>`)

**Problem**: Tooltip divs rendered inside paragraph tags caused SSR/client mismatch.

**Solution**: Use `createPortal(tooltip, document.body)` with a `mounted` state check:
```tsx
const [mounted, setMounted] = useState(false)
useEffect(() => { setMounted(true) }, [])

{mounted && showPreview && createPortal(<Tooltip />, document.body)}
```

### 2. TypeScript `unknown` to `ReactNode` Error

**Problem**: Metadata values typed as `unknown` couldn't render directly.

**Solution**: Explicit type casting with ternary:
```tsx
{citation.metadata.book_title ? ` · ${String(citation.metadata.book_title)}` : null}
```

### 3. Raw Search vs Synthesized Answers

**Problem**: Initial implementation returned raw chunks, not synthesized answers.

**Solution**: Added Claude API integration with structured prompts requiring citations.

### 4. Source Clustering by Author

**Problem**: Search results clustered around same author (e.g., 5 results from John Cutler).

**Solution**: Diversity algorithm limiting max 3 per author, max 2 per source title.

### 5. No User Feedback During Search

**Problem**: 3-5 second searches with no progress indication.

**Solution**: Multi-step progress indicator with checkmarks and progress bar.

## Prevention Strategies

1. **Portal Pattern for Tooltips**: Always use portals for hover elements to avoid DOM nesting issues
2. **Diversity by Default**: Over-fetch candidates (5x) and apply diversity filtering
3. **Explicit Type Casting**: Use `String()` for metadata values in JSX
4. **Environment Variables**: Check for API keys at startup, not request time
5. **Progress Feedback**: Any operation >1s should have progress indication

## File Structure

```
├── web/                              # Next.js (Vercel)
│   ├── app/page.tsx                  # Main chat UI with progress
│   ├── components/
│   │   ├── AnswerDisplay.tsx         # Markdown + citation badges
│   │   └── CitationCard.tsx          # Expandable source cards
│   ├── lib/api.ts                    # API client
│   └── next.config.js                # Backend proxy
│
├── api/                              # FastAPI (Railway/Fly.io)
│   ├── main.py                       # App entry with CORS
│   ├── routers/
│   │   ├── chat.py                   # RAG endpoint
│   │   └── search.py                 # Hybrid search + diversity
│   └── requirements.txt
```

## Deployment Recommendation

- **Frontend**: Vercel (free tier) - handles Next.js naturally
- **Backend**: Fly.io (free tier includes 3 VMs) or Railway ($5-20/mo)
- **Why split**: ChromaDB + embeddings exceed Vercel's 250MB limit

## Related Documentation

- `plans/distributed-dancing-rocket.md` - Original architecture plan
- `docs/decision-log.md` - Architecture decision records
