---
status: pending
priority: p3
issue_id: "010"
tags: [code-review, cleanup, dead-code]
dependencies: []
---

# Unused seenCitationsRef

## Problem Statement

A ref is declared for "O(1) deduplication" but is never used for any deduplication logic. It's only cleared in `startNewThread()` but never read.

## Findings

- **Location**: `web/app/page.tsx` line 116
- **Evidence**:
  ```typescript
  // Track seen citations for O(1) deduplication
  const seenCitationsRef = useRef<Set<string>>(new Set())
  ```
  Only usage (line 380):
  ```typescript
  seenCitationsRef.current.clear()
  ```
- **Impact**: Dead code, confusing for maintainers

## Proposed Solutions

### Option 1: Remove It (Recommended)
Delete the ref and its clear() call.
- **Pros**: Less code, clearer intent
- **Cons**: None
- **Effort**: Trivial
- **Risk**: None

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `web/app/page.tsx`
- **Lines to remove**: 116, 380

## Acceptance Criteria

- [ ] seenCitationsRef removed
- [ ] No functionality changes

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Remove unused code |

## Resources

- Simplicity review agent: a3d7cad
