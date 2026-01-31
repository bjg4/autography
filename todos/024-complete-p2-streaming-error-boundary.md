---
status: pending
priority: p2
issue_id: "024"
tags: [code-review, reliability]
dependencies: []
---

# Missing Error Boundary for Streaming

## Problem Statement

If the Anthropic stream fails mid-way (network error, timeout), the generator will raise an exception that won't be gracefully communicated to the frontend. Users see a broken/hanging response.

**Why it matters:** Users have no way to know if a response failed partway through streaming.

## Findings

**Location:** `api/routers/chat.py:353-395`

```python
async def generate():
    try:
        results = await engine.search_async(...)
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Search failed.'})}\n\n"
        return
    # ... no try/catch around stream iteration
    async with client.messages.stream(...) as stream:
        async for text in stream.text_stream:
            yield f"data: {json.dumps({'type': 'token', 'data': text})}\n\n"
```

The search has error handling, but the streaming loop doesn't.

## Proposed Solutions

### Solution A: Wrap Streaming Loop (Recommended)

```python
try:
    async with client.messages.stream(...) as stream:
        async for text in stream.text_stream:
            yield f"data: {json.dumps({'type': 'token', 'data': text})}\n\n"
except anthropic.APIError as e:
    print(f"[Chat] Stream interrupted: {e}")
    yield f"data: {json.dumps({'type': 'error', 'message': 'Stream interrupted. Please try again.'})}\n\n"
```

**Pros:** Simple fix, users get clear error message
**Cons:** None significant
**Effort:** Small
**Risk:** Low

## Technical Details

**Affected files:**
- `api/routers/chat.py`

## Acceptance Criteria

- [ ] Streaming errors yield a proper error event to frontend
- [ ] Frontend displays error message when stream fails
- [ ] Error is logged server-side

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-30 | Created from code review | Performance oracle identified missing error handling |

## Resources

- Performance review agent findings
