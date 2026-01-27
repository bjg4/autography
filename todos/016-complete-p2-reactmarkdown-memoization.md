---
status: pending
priority: p2
issue_id: "016"
tags: [code-review, performance, frontend]
dependencies: ["015"]
---

# ReactMarkdown Components Object Recreated on Every Render

## Problem Statement

The `components` object passed to ReactMarkdown is recreated on every render, causing ReactMarkdown to re-parse the entire markdown content even when it hasn't changed. Combined with the streaming re-render issue (#015), this multiplies performance impact.

## Findings

- **Location**: `web/components/AnswerDisplay.tsx` lines 167-179
- **Evidence**:
  ```typescript
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => <p>{processChildren(children)}</p>,
        li: ({ children }) => <li>{processChildren(children)}</li>,
        // ... recreated on every render
      }}
    >
      {answer}
    </ReactMarkdown>
  )
  ```
- **Impact**:
  - New object reference = ReactMarkdown thinks config changed
  - Full markdown re-parse on every render
  - With streaming: 2500+ full parses per response

## Proposed Solutions

### Option 1: useMemo for Components Object (Recommended)
```typescript
const markdownComponents = useMemo(() => ({
  p: ({ children }: { children: React.ReactNode }) => (
    <p>{processChildren(children)}</p>
  ),
  li: ({ children }: { children: React.ReactNode }) => (
    <li>{processChildren(children)}</li>
  ),
  strong: ({ children }: { children: React.ReactNode }) => (
    <strong>{processChildren(children)}</strong>
  ),
  em: ({ children }: { children: React.ReactNode }) => (
    <em>{processChildren(children)}</em>
  ),
}), [citationMap])  // Only recreate when citations change

return <ReactMarkdown components={markdownComponents}>{answer}</ReactMarkdown>
```
- **Pros**: Eliminates unnecessary re-parses
- **Cons**: None
- **Effort**: Small
- **Risk**: None

### Option 2: Extract Components to Module Level
```typescript
// Outside component
const markdownComponents = {
  p: ({ children }) => <p>{children}</p>,
  // ... but can't use citationMap
}
```
- **Pros**: Never recreated
- **Cons**: Can't access component state (citationMap)
- **Effort**: Small
- **Risk**: May break citation highlighting

## Recommended Action

Option 1 - useMemo with citationMap dependency

## Technical Details

- **Affected Files**: `web/components/AnswerDisplay.tsx`
- **Components**: AnswerDisplay

## Acceptance Criteria

- [ ] ReactMarkdown components memoized
- [ ] Citation highlighting still works
- [ ] No re-parse when only answer text changes

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from performance review | Memoize objects passed to expensive components |

## Resources

- Performance review agent: a3fe44d
- React useMemo docs: https://react.dev/reference/react/useMemo
