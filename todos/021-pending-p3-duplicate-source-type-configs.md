---
status: pending
priority: p3
issue_id: "021"
tags: [code-review, duplication, frontend]
dependencies: []
---

# Duplicate Source Type Configuration

## Problem Statement

Source type icons and labels are defined in multiple places with nearly identical content. This creates maintenance burden and risk of inconsistency.

## Findings

- **Locations**:
  - `web/app/page.tsx` lines 24-28 (sourceTypeConfig)
  - `web/components/CitationCard.tsx` lines 15-25 (typeIcons, typeLabels)
- **Evidence**:
  ```typescript
  // page.tsx
  const sourceTypeConfig: Record<string, { icon: string; label: string }> = {
    blog: { icon: '📝', label: 'Blog' },
    book_chapter: { icon: '📖', label: 'Book' },
    // ...
  }

  // CitationCard.tsx
  const typeIcons: Record<string, string> = {
    blog: '📝',
    book_chapter: '📖',
    // ...
  }
  const typeLabels: Record<string, string> = {
    blog: 'Blog',
    book_chapter: 'Book',
    // ...
  }
  ```
- **Impact**: Must update both places when adding source types

## Proposed Solutions

### Option 1: Extract to Shared Constants (Recommended)
```typescript
// web/lib/constants.ts
export const SOURCE_TYPE_CONFIG: Record<string, { icon: string; label: string }> = {
  blog: { icon: '📝', label: 'Blog' },
  book_chapter: { icon: '📖', label: 'Book' },
  podcast_transcript: { icon: '🎙️', label: 'Podcast' },
}
```
- **Pros**: Single source of truth
- **Cons**: New file
- **Effort**: Small
- **Risk**: None

## Recommended Action

Option 1 - Extract to shared constants

## Technical Details

- **Affected Files**:
  - New: `web/lib/constants.ts`
  - Modified: `web/app/page.tsx`, `web/components/CitationCard.tsx`

## Acceptance Criteria

- [ ] Single source type config shared across components
- [ ] All usages updated to import from constants
- [ ] No duplicate definitions

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from pattern review | Consolidate repeated config |

## Resources

- Pattern review agent: af7110e
