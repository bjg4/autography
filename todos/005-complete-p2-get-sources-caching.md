---
status: pending
priority: p2
issue_id: "005"
tags: [code-review, performance]
dependencies: []
---

# get_sources() Iterates All Documents on Every Call

## Problem Statement

The `get_sources()` method iterates through all 12,486 document metadata entries on every API call to compute source types and authors. This data is static and should be cached at initialization.

## Findings

- **Location**: `api/routers/search.py` lines 247-264
- **Evidence**:
  ```python
  def get_sources(self) -> dict:
      source_types = set()
      authors = set()
      for meta in self.doc_metadatas:  # O(n) on every call!
          if meta.get('source_type'):
              source_types.add(meta['source_type'])
          if meta.get('author'):
              authors.add(meta['author'])
      return {...}
  ```
- **Current Impact**: ~5ms per call, called on every page load
- **At 100x scale**: ~500ms per call

## Proposed Solutions

### Option 1: Cache at Initialization (Recommended)
```python
def __init__(self, ...):
    # ... existing init ...
    self._sources_cache = self._compute_sources()

def _compute_sources(self) -> dict:
    source_types = set()
    authors = set()
    for meta in self.doc_metadatas:
        # ... same logic ...
    return {...}

def get_sources(self) -> dict:
    return self._sources_cache  # O(1)
```
- **Pros**: Trivial change, O(1) lookup
- **Cons**: None
- **Effort**: Small
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `api/routers/search.py`
- **Components**: HybridSearch.get_sources

## Acceptance Criteria

- [ ] Sources computed once at init, not on every request
- [ ] /api/sources response time < 5ms
- [ ] Existing functionality unchanged

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Cache static computations |

## Resources

- Performance review agent: a3c29d1
