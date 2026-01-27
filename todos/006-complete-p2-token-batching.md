---
status: pending
priority: p2
issue_id: "006"
tags: [code-review, performance, frontend]
dependencies: []
---

# Streaming Triggers Re-render Per Token

## Problem Statement

Each streaming token (~50-100 per response) triggers a React state update and full component re-render. With 10-20 tokens per second during streaming, this causes 10-20 re-renders per second.

## Findings

- **Location**: `web/app/page.tsx` lines 340-343
- **Evidence**:
  ```typescript
  onToken: (token) => {
    finalAnswer += token
    setStreamingAnswer(prev => prev + token)  // State update per token!
  },
  ```
- **Impact**:
  - Janky UI during streaming
  - High CPU usage
  - Combined with AnswerDisplay re-parsing markdown, compounds the problem

## Proposed Solutions

### Option 1: RAF Batching (Recommended)
```typescript
const pendingTokens = useRef('')
const rafId = useRef<number>()

onToken: (token) => {
  finalAnswer += token
  pendingTokens.current += token

  if (!rafId.current) {
    rafId.current = requestAnimationFrame(() => {
      setStreamingAnswer(prev => prev + pendingTokens.current)
      pendingTokens.current = ''
      rafId.current = undefined
    })
  }
},
```
- **Pros**: Batches updates to ~60fps max, smooth UI
- **Cons**: Slight delay in display (1 frame)
- **Effort**: Small
- **Risk**: Low

### Option 2: Use a Ref for Display
- **Pros**: No re-renders during streaming
- **Cons**: More complex, need manual DOM updates
- **Effort**: Medium
- **Risk**: Medium

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `web/app/page.tsx`
- **Components**: handleSubmit streaming logic

## Acceptance Criteria

- [ ] Re-renders during streaming capped at ~60/second
- [ ] UI feels smooth during token streaming
- [ ] No visible delay in token display

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Batch state updates for animations |

## Resources

- requestAnimationFrame: https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame
- Performance review agent: a3c29d1
