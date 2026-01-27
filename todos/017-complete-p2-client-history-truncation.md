---
status: pending
priority: p2
issue_id: "017"
tags: [code-review, performance, frontend]
dependencies: []
---

# Client Sends Full Conversation History (Only Last 3 Used)

## Problem Statement

The frontend sends the ENTIRE conversation thread history on every chat request, but the backend only uses the last 3 turns. This causes unnecessary data transfer, especially in long conversations.

## Findings

- **Location**:
  - `web/app/page.tsx` lines 333-338 (client sends all)
  - `api/routers/chat.py` lines 199-204 (server uses last 3)
- **Evidence**:
  ```typescript
  // Client sends everything
  const getHistory = (): ConversationTurn[] => {
    return thread.map(item => ({
      question: item.question,
      answer: item.response.answer
    }))
  }
  ```
  ```python
  # Server only uses last 3
  recent_history = chat_request.history[-3:]
  ```
- **Impact**:
  - 10-turn thread at ~2KB/turn = 20KB payload
  - 50-turn thread = 100KB+ per request
  - Wasted bandwidth and serialization

## Proposed Solutions

### Option 1: Truncate on Client (Recommended)
```typescript
const getHistory = (): ConversationTurn[] => {
  return thread.slice(-3).map(item => ({
    question: item.question,
    answer: item.response.answer
  }))
}
```
- **Pros**: Simple, immediate fix
- **Cons**: None
- **Effort**: Trivial
- **Risk**: None

### Option 2: Server-Side Thread Storage
- Store threads in backend, send only thread ID
- **Pros**: Better for long conversations
- **Cons**: Requires database, session management
- **Effort**: Large
- **Risk**: Medium

## Recommended Action

Option 1 - Truncate on client

## Technical Details

- **Affected Files**: `web/app/page.tsx`
- **Components**: getHistory helper function

## Acceptance Criteria

- [ ] Client sends max 3 conversation turns
- [ ] Response quality unchanged
- [ ] Request payload size reduced

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from performance review | Match client behavior to server expectations |

## Resources

- Performance review agent: a3fe44d
