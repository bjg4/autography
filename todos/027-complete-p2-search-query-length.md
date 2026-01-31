---
status: pending
priority: p2
issue_id: "027"
tags: [code-review, security]
dependencies: []
---

# Missing Query Length Limit in Search Endpoint

## Problem Statement

The search query field has no `max_length` constraint, allowing extremely large queries that could cause:
- Memory exhaustion during BM25 tokenization
- CPU exhaustion during embedding generation
- Potential denial of service

## Findings

**Location:** `api/routers/search.py:36`

```python
query: str = Field(..., min_length=1, description="Search query")
```

Compare to the chat endpoint which properly limits input:

```python
# chat.py:82
question: str = Field(..., min_length=1, max_length=10000, description="User's question")
```

## Proposed Solutions

### Solution A: Add max_length (Recommended)

```python
query: str = Field(..., min_length=1, max_length=10000, description="Search query")
```

**Pros:** Consistent with chat endpoint, prevents DoS
**Cons:** None
**Effort:** Tiny
**Risk:** None

## Technical Details

**Affected files:**
- `api/routers/search.py`

## Acceptance Criteria

- [ ] SearchRequest.query has max_length=10000
- [ ] Oversized queries return 422 validation error

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-30 | Created from code review | Security sentinel identified missing validation |

## Resources

- Security review findings
