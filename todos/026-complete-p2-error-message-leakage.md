---
status: pending
priority: p2
issue_id: "026"
tags: [code-review, security]
dependencies: []
---

# Error Message Information Leakage

## Problem Statement

The error handler exposes internal error details to clients, potentially leaking:
- API configuration details
- Internal service names and endpoints
- Stack trace information
- Information useful for attack reconnaissance

## Findings

**Location:** `api/routers/chat.py:241-244`

```python
except anthropic.APIError as e:
    raise HTTPException(
        status_code=502,
        detail=f"AI service error: {str(e)}"
    )
```

The `str(e)` may contain internal details that shouldn't be exposed to end users.

## Proposed Solutions

### Solution A: Generic User-Facing Messages (Recommended)

```python
except anthropic.APIError as e:
    print(f"[Chat] Anthropic API error: {type(e).__name__}: {e}")
    raise HTTPException(
        status_code=502,
        detail="AI service temporarily unavailable"
    )
```

**Pros:** No information leakage, errors still logged server-side
**Cons:** Less specific user-facing errors
**Effort:** Small
**Risk:** Low

## Technical Details

**Affected files:**
- `api/routers/chat.py`

## Acceptance Criteria

- [ ] API error messages are generic for users
- [ ] Detailed errors logged server-side
- [ ] No internal details exposed in HTTP responses

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-30 | Created from code review | Security sentinel identified info leakage |

## Resources

- Security review findings
