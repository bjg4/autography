---
status: pending
priority: p2
issue_id: "023"
tags: [code-review, performance]
dependencies: []
---

# Unbatched Chroma Fetches in Parent Span Expansion

## Problem Statement

For each search result (typically 8-10), `_expand_to_parent_span` makes a separate Chroma query. This means 8-10 sequential database round trips per search request.

**Why it matters:** At scale, this becomes a major bottleneck. Each user search triggers ~10 Chroma queries, leading to connection pool exhaustion and increased latency.

## Findings

**Location:** `api/routers/search.py:363-369`

```python
# Get content - expand to parent span if enabled
if expand_spans:
    content = self._expand_to_parent_span(doc_id)
else:
    texts = self._get_texts_by_ids([doc_id])
    content = texts.get(doc_id, "")
```

**Current Impact:** O(n) database calls where n = number of results.

## Proposed Solutions

### Solution A: Batch Upfront (Recommended)
Collect all needed chunk IDs across all spans first, then make a single Chroma call.

```python
def _apply_filters_and_diversity(self, ranked, n_results, ...):
    # Phase 1: Collect all needed chunk IDs
    needed_chunk_ids = set()
    result_candidates = []

    for doc_id, score in ranked:
        span_id = metadata.get('parent_span_id')
        if span_id and span_id in self.parent_span_to_chunks:
            chunk_ids = [self.doc_ids[i] for i in self.parent_span_to_chunks[span_id]]
            needed_chunk_ids.update(chunk_ids)
            result_candidates.append((doc_id, score, metadata, chunk_ids))

    # Phase 2: Single batched fetch
    all_texts = self._get_texts_by_ids(list(needed_chunk_ids))

    # Phase 3: Stitch results using cached texts
    ...
```

**Pros:** 8-10x reduction in database round trips
**Cons:** More complex code, slightly more memory for text cache
**Effort:** Medium
**Risk:** Low

## Technical Details

**Affected files:**
- `api/routers/search.py`

## Acceptance Criteria

- [ ] Parent span expansion uses single batched Chroma fetch
- [ ] Search latency reduced by measurable amount
- [ ] No change to search result quality

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-30 | Created from code review | Performance oracle identified this as critical bottleneck |

## Resources

- Performance review agent findings
