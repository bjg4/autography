---
status: pending
priority: p2
issue_id: "008"
tags: [code-review, architecture, duplication]
dependencies: []
---

# Duplicate HybridSearch Implementation

## Problem Statement

The `HybridSearch` class is implemented in two places with nearly identical code. The API version has additional features (security validation, diversity filtering) but the core search logic is duplicated.

## Findings

- **Locations**:
  - `ingestion/hybrid_search.py` (lines 19-242) - 223 lines
  - `api/routers/search.py` (lines 64-265) - 201 lines
- **Evidence**: Both implement:
  - `_semantic_search()`
  - `_bm25_search()`
  - `_reciprocal_rank_fusion()`
  - `search()` with filters
- **Impact**: Bug fixes must be applied twice, divergence risk

## Proposed Solutions

### Option 1: Create Shared Core Module (Recommended)
```
core/
  search/
    __init__.py
    hybrid_search.py  # Shared implementation
    security.py       # API-specific validation
```
Both `ingestion/` and `api/` import from `core/`

- **Pros**: Single source of truth, testable
- **Cons**: Requires package restructuring
- **Effort**: Medium
- **Risk**: Low

### Option 2: Make API Version the Canonical One
- **Pros**: Simpler, one direction
- **Cons**: Ingestion scripts need to call API or import from api/
- **Effort**: Small
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**:
  - `ingestion/hybrid_search.py`
  - `api/routers/search.py`
  - New `core/` module
- **Components**: HybridSearch class

## Acceptance Criteria

- [ ] Single HybridSearch implementation
- [ ] Both API and ingestion use same code
- [ ] All existing tests pass

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | DRY - Don't Repeat Yourself |

## Resources

- Pattern review agent: a7f22f7
