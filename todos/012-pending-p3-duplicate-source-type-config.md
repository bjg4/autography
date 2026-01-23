---
status: pending
priority: p3
issue_id: "012"
tags: [code-review, duplication, frontend]
dependencies: []
---

# Duplicate Source Type Configuration

## Problem Statement

Source type styling is defined in multiple places with slightly different structures, leading to inconsistency risk.

## Findings

- **Locations**:
  - `web/app/page.tsx` lines 23-27: `sourceTypeConfig`
  - `web/components/CitationCard.tsx` lines 15-24: `typeIcons` and `typeLabels`
- **Evidence**:
  ```typescript
  // page.tsx
  const sourceTypeConfig: Record<string, { label: string; color: string }> = {
    essay: { label: 'Essay', color: 'bg-blue-50 text-blue-600' },
    // ...
  }

  // CitationCard.tsx
  const typeIcons: Record<string, string> = { essay: '...' }
  const typeLabels: Record<string, string> = { essay: 'Essay' }
  ```

## Proposed Solutions

### Option 1: Create Shared Constants (Recommended)
```typescript
// lib/constants.ts
export const SOURCE_TYPES = {
  essay: { label: 'Essay', icon: '...', color: 'bg-blue-50 text-blue-600' },
  book_chapter: { ... },
  podcast_transcript: { ... },
} as const
```
- **Pros**: Single source of truth
- **Cons**: Minor refactor
- **Effort**: Small
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**:
  - `web/app/page.tsx`
  - `web/components/CitationCard.tsx`
  - New `web/lib/constants.ts`

## Acceptance Criteria

- [ ] Source type config in single location
- [ ] Both components use shared config
- [ ] Styling consistent across app

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | DRY applies to config too |

## Resources

- Pattern review agent: a7f22f7
