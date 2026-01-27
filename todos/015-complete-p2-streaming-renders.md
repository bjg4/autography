---
status: pending
priority: p2
issue_id: "015"
tags: [code-review, performance, frontend]
dependencies: []
---

# Streaming SSE Causes Excessive React Re-renders

## Problem Statement

Each token from the streaming response triggers a React state update and full ReactMarkdown re-parse. A 1,500 word response causes 2,500+ re-renders, blocking the JavaScript thread and causing UI jank on mobile devices.

## Findings

- **Location**: `web/app/page.tsx` lines 391-393
- **Evidence**:
  ```typescript
  onToken: (token) => {
    finalAnswer += token
    setStreamingAnswer(prev => prev + token)  // Re-render on EVERY token
  },
  ```
- **Impact**:
  - ~2,500 re-renders per response
  - Each render triggers ReactMarkdown parsing of entire accumulated answer
  - 500-2000ms of JavaScript execution blocking
  - Mobile: dropped frames, jank, potential ANR

## Proposed Solutions

### Option 1: Batch Updates with requestAnimationFrame (Recommended)
```typescript
const tokenBufferRef = useRef('')
const rafRef = useRef<number>()

onToken: (token) => {
  tokenBufferRef.current += token

  if (!rafRef.current) {
    rafRef.current = requestAnimationFrame(() => {
      setStreamingAnswer(prev => prev + tokenBufferRef.current)
      tokenBufferRef.current = ''
      rafRef.current = undefined
    })
  }
}
```
- **Pros**: ~60 updates/sec instead of 2500+, matches display refresh
- **Cons**: Slight perceived latency (max 16ms)
- **Effort**: Small
- **Risk**: Low

### Option 2: Debounce State Updates
```typescript
const debouncedUpdate = useMemo(
  () => debounce((text: string) => setStreamingAnswer(text), 50),
  []
)

onToken: (token) => {
  finalAnswer += token
  debouncedUpdate(finalAnswer)
}
```
- **Pros**: Simple
- **Cons**: 50ms latency feels less responsive
- **Effort**: Small
- **Risk**: Low

## Recommended Action

Option 1 - requestAnimationFrame batching

## Technical Details

- **Affected Files**: `web/app/page.tsx`
- **Components**: handleSubmit streaming handler, AnswerDisplay

## Acceptance Criteria

- [ ] Token updates batched to ~60/sec max
- [ ] No visible delay in text appearance
- [ ] Mobile performance improved (no jank)
- [ ] Memory usage stable during streaming

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from performance review | Batch rapid state updates |

## Resources

- Performance review agent: a3fe44d
