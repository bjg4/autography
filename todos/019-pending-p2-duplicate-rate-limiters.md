---
status: pending
priority: p2
issue_id: "019"
tags: [code-review, architecture, backend]
dependencies: []
---

# Duplicate Rate Limiter Instances Across Modules

## Problem Statement

Each router module creates its own `Limiter` instance. This may cause rate limits to not be shared correctly across endpoints, and creates unnecessary duplication.

## Findings

- **Locations**:
  - `api/main.py` line 55: `limiter = Limiter(key_func=get_remote_address)`
  - `api/routers/search.py` line 24: `limiter = Limiter(key_func=get_remote_address)`
  - `api/routers/chat.py` line 23: `limiter = Limiter(key_func=get_remote_address)`
- **Evidence**: Three separate limiter instances with identical configuration
- **Impact**:
  - Rate limits may not be shared correctly
  - Confusing code organization
  - If slowapi stores state in limiter, limits might not work as expected

## Proposed Solutions

### Option 1: Centralize Limiter in Shared Module (Recommended)
```python
# api/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```
```python
# api/routers/chat.py
from rate_limit import limiter

@router.post("/chat")
@limiter.limit("10/minute")
async def chat(...):
```
- **Pros**: Single source of truth, clearer rate limit behavior
- **Cons**: Minor refactor
- **Effort**: Small
- **Risk**: Low

### Option 2: Use main.py Limiter via app.state
```python
# api/main.py
app.state.limiter = Limiter(...)

# api/routers/chat.py
@router.post("/chat")
async def chat(request: Request):
    limiter = request.app.state.limiter
```
- **Pros**: No import needed
- **Cons**: Less explicit, decorator pattern harder
- **Effort**: Medium
- **Risk**: Low

## Recommended Action

Option 1 - Create shared rate_limit.py module

## Technical Details

- **Affected Files**:
  - New: `api/rate_limit.py`
  - Modified: `api/main.py`, `api/routers/chat.py`, `api/routers/search.py`
- **Components**: Limiter configuration

## Acceptance Criteria

- [ ] Single limiter instance shared across all endpoints
- [ ] Rate limits work correctly across endpoints
- [ ] No duplicate limiter imports

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from architecture review | Centralize shared resources |

## Resources

- Architecture review agent: adc2d7e
- slowapi docs: https://github.com/laurentS/slowapi
