---
title: "perf: Parallel Hybrid Search"
type: perf
date: 2026-01-28
---

# perf: Parallel Hybrid Search

## Problem

Semantic and BM25 searches run sequentially in `HybridSearch.search()`, adding unnecessary latency to time-to-first-token (TTFT).

```python
# Current: sequential (lines 193-195 of search.py)
semantic_results = self._semantic_search(query, n_candidates)
bm25_results = self._bm25_search(query, n_candidates)
```

## Solution

Run both searches in parallel using `asyncio.gather` with `asyncio.to_thread` (since both are CPU-bound operations).

**Expected impact:** 50-100ms reduction in search phase duration.

## Implementation

### 1. Add async search method to `api/routers/search.py`

```python
import asyncio

async def search_async(
    self,
    query: str,
    n_results: int = 10,
    # ... same params as search()
) -> list[dict]:
    """Async version with parallel semantic + BM25 search."""
    n_candidates = n_results * 5

    if mode == "semantic":
        ranked = await asyncio.to_thread(self._semantic_search, query, n_candidates)
    elif mode == "bm25":
        ranked = await asyncio.to_thread(self._bm25_search, query, n_candidates)
    else:
        # Parallel execution
        semantic_results, bm25_results = await asyncio.gather(
            asyncio.to_thread(self._semantic_search, query, n_candidates),
            asyncio.to_thread(self._bm25_search, query, n_candidates),
        )
        ranked = self._reciprocal_rank_fusion(semantic_results, bm25_results)

    # ... rest unchanged (filtering, diversity, etc.)
```

### 2. Update callers in `api/routers/chat.py`

```python
# Line 170: /chat endpoint
results = await engine.search_async(...)

# Line 264: /chat/stream endpoint
results = await engine.search_async(...)
```

### 3. Keep sync `search()` for backwards compatibility

The `/api/search` endpoint can continue using sync `search()` since it's not on the critical path for chat TTFT.

## Acceptance Criteria

- [ ] Chat endpoints use `search_async()` with parallel execution
- [ ] Search phase duration reduced (verify with timing logs)
- [ ] No regressions - all existing functionality works
- [ ] Sync `search()` remains available for non-chat callers

## Review Feedback Applied

This plan was reviewed by DHH, Kieran, and Simplicity reviewers. Original plan had 4 optimizations; 3 were cut:

| Cut | Reason |
|-----|--------|
| Pre-warm embedding model | UptimeRobot already prevents cold starts |
| Anthropic prompt caching | System prompt is only ~400 tokens; context dominates |
| Reduce sources 8→6 | Wrong tradeoff - quality degradation for microseconds |

The parallel search optimization was the only one all reviewers agreed to keep.
