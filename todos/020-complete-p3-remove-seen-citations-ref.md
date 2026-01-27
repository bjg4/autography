---
status: pending
priority: p3
issue_id: "020"
tags: [code-review, cleanup, frontend]
dependencies: []
---

# Dead Code: seenCitationsRef Declared But Never Used

## Problem Statement

The `seenCitationsRef` is declared and cleared in `startNewThread` but is never read anywhere in the code. This is dead code that should be removed.

## Findings

- **Location**: `web/app/page.tsx` lines 163-164
- **Evidence**:
  ```typescript
  const seenCitationsRef = useRef<Set<number>>(new Set())
  // ...
  const startNewThread = () => {
    // ...
    seenCitationsRef.current.clear()  // Cleared but never read
  }
  ```
- **Impact**: Minor code clutter, confusing for readers

## Proposed Solutions

### Option 1: Remove Dead Code (Recommended)
- Delete `seenCitationsRef` declaration
- Remove `.clear()` call in `startNewThread`
- **Pros**: Clean code
- **Cons**: None
- **Effort**: Trivial
- **Risk**: None

## Recommended Action

Option 1 - Remove the dead code

## Technical Details

- **Affected Files**: `web/app/page.tsx`
- **Lines to Remove**: 163-164, and reference in startNewThread

## Acceptance Criteria

- [ ] seenCitationsRef removed
- [ ] No functional changes
- [ ] Code compiles without errors

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from simplicity review | Remove unused code |

## Resources

- Simplicity review agent: a9fc47d
