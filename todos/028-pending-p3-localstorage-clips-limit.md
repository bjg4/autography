---
status: pending
priority: p3
issue_id: "028"
tags: [code-review, reliability]
dependencies: []
---

# localStorage Clips Has No Size Limit

## Problem Statement

Clips are persisted to localStorage without any size limit. Users can clip large text selections repeatedly, eventually hitting localStorage's ~5MB limit and causing silent failures.

## Findings

**Location:** `web/app/page.tsx:191-195`

```typescript
useEffect(() => {
  if (clipsLoaded) {
    localStorage.setItem('autography-clips', JSON.stringify(clips))
  }
}, [clips, clipsLoaded])
```

No validation on clip count or individual clip size.

## Proposed Solutions

### Solution A: Add Size Limits

```typescript
const MAX_CLIPS = 100
const MAX_CLIP_LENGTH = 2000

const newClip = {
  text: textToClip.slice(0, MAX_CLIP_LENGTH),
  ...
}
setClips(prev => [newClip, ...prev].slice(0, MAX_CLIPS))
```

**Pros:** Prevents localStorage overflow
**Cons:** May truncate user-selected text
**Effort:** Small
**Risk:** Low

## Technical Details

**Affected files:**
- `web/app/page.tsx`

## Acceptance Criteria

- [ ] Maximum 100 clips stored
- [ ] Individual clips truncated to reasonable size
- [ ] User notified if clip was truncated

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-30 | Created from code review | Performance oracle identified potential overflow |

## Resources

- Performance review findings
