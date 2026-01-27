---
status: pending
priority: p2
issue_id: "018"
tags: [code-review, performance, frontend]
dependencies: []
---

# N IntersectionObservers Created Instead of One

## Problem Statement

The code creates a separate IntersectionObserver for each thread item instead of using a single observer that observes multiple elements. This adds overhead and observers are recreated every time thread length changes.

## Findings

- **Location**: `web/app/page.tsx` lines 193-216
- **Evidence**:
  ```typescript
  useEffect(() => {
    const observers: IntersectionObserver[] = []

    responseRefs.current.forEach((ref, index) => {
      if (ref) {
        const observer = new IntersectionObserver(  // One per element!
          (entries) => { /* ... */ },
          { threshold: [0.3, 0.5, 0.7], rootMargin: '-100px 0px -100px 0px' }
        )
        observer.observe(ref)
        observers.push(observer)
      }
    })

    return () => observers.forEach(observer => observer.disconnect())
  }, [thread.length])
  ```
- **Impact**:
  - 20-item thread = 20 separate observers
  - Each observer has calculation overhead
  - All observers recreated when thread grows

## Proposed Solutions

### Option 1: Single Observer, Multiple Targets (Recommended)
```typescript
useEffect(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
          const index = responseRefs.current.indexOf(entry.target as HTMLDivElement)
          if (index !== -1) setVisibleResponseIndex(index)
        }
      })
    },
    { threshold: [0.3, 0.5, 0.7], rootMargin: '-100px 0px -100px 0px' }
  )

  responseRefs.current.forEach((ref) => ref && observer.observe(ref))
  return () => observer.disconnect()
}, [thread.length])
```
- **Pros**: Single observer, less overhead
- **Cons**: Slightly different callback structure
- **Effort**: Small
- **Risk**: Low

## Recommended Action

Option 1 - Single observer with multiple targets

## Technical Details

- **Affected Files**: `web/app/page.tsx`
- **Components**: Visibility tracking useEffect

## Acceptance Criteria

- [ ] Single IntersectionObserver used
- [ ] Visibility tracking still works correctly
- [ ] Memory usage stable with long threads

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from performance review | One observer can watch many elements |

## Resources

- Performance review agent: a3fe44d
- IntersectionObserver API: https://developer.mozilla.org/en-US/docs/Web/API/IntersectionObserver
