---
status: pending
priority: p2
issue_id: "007"
tags: [code-review, architecture, refactor]
dependencies: []
---

# God Component - page.tsx is 835 Lines

## Problem Statement

The main page component handles too many responsibilities: thread management, streaming, visibility tracking, clips/bookmarking, text selection, source cards, form submission, and sidebar citations. This makes the code difficult to maintain, test, and debug.

## Findings

- **Location**: `web/app/page.tsx` (entire file)
- **Evidence**:
  - 18 separate useState hooks (lines 89-116)
  - 7 useEffect hooks (lines 119-210)
  - Inline SourceCard component (lines 29-86)
  - Multiple features: threading, clips, streaming, IntersectionObserver
- **Code Metrics**:
  - 835 lines total
  - 18 state variables
  - 7 side effects
  - 1 inline component definition

## Proposed Solutions

### Option 1: Extract Custom Hooks (Recommended)
Create focused hooks:
- `useClips()` - clip state + localStorage sync
- `useStreaming()` - streaming answer state
- `useVisibility()` - IntersectionObserver logic

Then extract components:
- `SourceCard.tsx` (already inline, just move)
- `ChatThread.tsx` - thread display
- `ClipsDrawer.tsx` - clips UI

- **Pros**: Incremental, testable, clear responsibilities
- **Cons**: Takes time
- **Effort**: Medium
- **Risk**: Low

### Option 2: Use State Machine
- **Pros**: Clearer state transitions
- **Cons**: Bigger refactor, learning curve
- **Effort**: Large
- **Risk**: Medium

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `web/app/page.tsx`, new hook/component files
- **Components**: Home page and all extracted pieces

## Acceptance Criteria

- [ ] page.tsx under 400 lines
- [ ] SourceCard moved to components/
- [ ] At least 2 custom hooks extracted
- [ ] All existing functionality preserved

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Single Responsibility Principle applies to components |

## Resources

- React custom hooks: https://react.dev/learn/reusing-logic-with-custom-hooks
- Architecture review agent: a06db43
- Pattern review agent: a7f22f7
