---
status: pending
priority: p2
issue_id: "004"
tags: [code-review, performance, algorithm]
dependencies: []
---

# O(n log n) BM25 Score Computation on Every Search

## Problem Statement

The BM25 search computes scores for ALL 12,486 documents and performs a full sort on every query. This is O(n log n) when only the top-k results are needed.

## Findings

- **Location**: `api/routers/search.py` lines 139-147
- **Evidence**:
  ```python
  scores = self.bm25.get_scores(tokenized_query)  # O(n) - scores all docs
  scored_docs = [(self.doc_ids[i], scores[i]) for i in range(len(scores))]  # Creates 12K tuples
  scored_docs.sort(key=lambda x: x[1], reverse=True)  # O(n log n) full sort
  return scored_docs[:n]  # Only need top-n
  ```
- **Current Impact**: ~15ms per search
- **At 100x scale**: Could be 1-2 seconds per search

## Proposed Solutions

### Option 1: Use numpy.argpartition (Recommended)
```python
import numpy as np

def _bm25_search(self, query: str, n: int):
    scores = self.bm25.get_scores(tokenized_query)
    top_indices = np.argpartition(scores, -n)[-n:]  # O(n)
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]  # O(k log k)
    return [(self.doc_ids[i], scores[i]) for i in top_indices]
```
- **Pros**: O(n) instead of O(n log n), minimal code change
- **Cons**: Adds numpy dependency (likely already present)
- **Effort**: Small
- **Risk**: Low

### Option 2: Use heapq.nlargest
- **Pros**: No numpy needed, stdlib only
- **Cons**: Slightly more complex
- **Effort**: Small
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `api/routers/search.py`
- **Components**: HybridSearch._bm25_search

## Acceptance Criteria

- [ ] Search time reduced by at least 30%
- [ ] Results are identical to current implementation
- [ ] Performance tested with 12,486 docs

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Partial sort for top-k is always faster |

## Resources

- numpy.argpartition: https://numpy.org/doc/stable/reference/generated/numpy.argpartition.html
- Performance review agent: a3c29d1
