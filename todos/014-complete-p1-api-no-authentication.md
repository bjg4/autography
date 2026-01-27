---
status: pending
priority: p1
issue_id: "014"
tags: [code-review, security, authentication]
dependencies: ["013"]
---

# API Endpoints Have No Authentication

## Problem Statement

All API endpoints (`/api/search`, `/api/chat`, `/api/chat/stream`) are publicly accessible with only rate limiting as protection. Anyone can bypass the UI password gate and access the API directly, consuming Anthropic API credits and extracting knowledge base content.

## Findings

- **Location**: `api/routers/chat.py`, `api/routers/search.py`
- **Evidence**:
  ```python
  @router.post("/chat", response_model=ChatResponse)
  @limiter.limit("10/minute")
  async def chat(chat_request: ChatRequest, request: Request):
      # No authentication check - anyone can call this
  ```
- **Impact**:
  - Anthropic API costs from unauthorized usage
  - Knowledge base content can be extracted via search
  - Rate limiting alone doesn't prevent determined abuse

## Proposed Solutions

### Option 1: API Key Header Authentication (Recommended for Internal Use)
```python
from fastapi import Header, HTTPException

async def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.environ.get("AUTOGRAPHY_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@router.post("/chat")
async def chat(request: ChatRequest, api_key: str = Depends(require_api_key)):
    ...
```
- **Pros**: Simple, works for agents and internal tools
- **Cons**: Key must be distributed to clients
- **Effort**: Small
- **Risk**: Low

### Option 2: Session-Based Auth (Ties to Password Gate)
- Validate password server-side, return session token
- Require session token on subsequent requests
- **Pros**: Links to existing password UI
- **Cons**: More complex, state management needed
- **Effort**: Medium
- **Risk**: Low

### Option 3: Accept Public API with Rate Limiting Only
- Document that API is intentionally public
- Rely on rate limiting (10 chat/min, 30 search/min)
- **Pros**: Simplest, agent-friendly
- **Cons**: No protection against abuse
- **Effort**: None
- **Risk**: Medium (cost exposure)

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**:
  - `api/main.py`
  - `api/routers/chat.py`
  - `api/routers/search.py`
- **Components**: FastAPI middleware, authentication dependency

## Acceptance Criteria

- [ ] Decision made on authentication approach
- [ ] If adding auth, all expensive endpoints require valid credentials
- [ ] If keeping public, document in README/API docs
- [ ] Rate limit headers exposed for client self-throttling

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from security review | Decide on auth before scaling |

## Resources

- Security review agent: acae90f
- FastAPI security docs: https://fastapi.tiangolo.com/tutorial/security/
