---
status: pending
priority: p3
issue_id: "022"
tags: [code-review, duplication, backend]
dependencies: []
---

# Duplicate Logic Between /chat and /chat/stream Endpoints

## Problem Statement

The `/chat` and `/chat/stream` endpoints duplicate the search retrieval and message building logic. This creates maintenance burden and risk of inconsistency.

## Findings

- **Location**: `api/routers/chat.py`
  - Lines 157-221 (/chat endpoint)
  - Lines 252-317 (/chat/stream endpoint)
- **Evidence**: Nearly identical code for:
  - Search retrieval (lines 169-176 vs 263-270)
  - Message building with history (lines 197-212 vs 274-290)
- **Impact**: Changes must be made in two places

## Proposed Solutions

### Option 1: Extract Shared Helper Function (Recommended)
```python
async def _prepare_chat_context(
    chat_request: ChatRequest
) -> tuple[list[dict], list[Citation], str]:
    """Prepare messages and citations for chat endpoints."""
    engine = get_search_engine()
    results = engine.search(
        query=chat_request.question,
        n_results=chat_request.n_sources,
        source_types=chat_request.source_types,
        authors=chat_request.authors,
        mode="hybrid"
    )

    context, citations = format_sources_for_context(results)

    messages = []
    if chat_request.history:
        for turn in chat_request.history[-3:]:
            messages.append({"role": "user", "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})

    user_message = f"{chat_request.question}\n\nHere's what I found:\n\n{context}"
    messages.append({"role": "user", "content": user_message})

    return messages, citations, context
```
- **Pros**: Single source of truth, ~30 LOC saved
- **Cons**: Minor refactor
- **Effort**: Small
- **Risk**: Low

## Recommended Action

Option 1 - Extract shared helper

## Technical Details

- **Affected Files**: `api/routers/chat.py`
- **Components**: /chat and /chat/stream endpoints

## Acceptance Criteria

- [ ] Shared helper function extracts common logic
- [ ] Both endpoints use the helper
- [ ] No duplicate search/message building code
- [ ] Behavior unchanged

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from simplicity review | DRY principle |

## Resources

- Simplicity review agent: a9fc47d
- Architecture review agent: adc2d7e
