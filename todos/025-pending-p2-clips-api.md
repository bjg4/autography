---
status: pending
priority: p2
issue_id: "025"
tags: [code-review, agent-native]
dependencies: []
---

# Clips Feature is localStorage-Only (Not Agent-Accessible)

## Problem Statement

The Clips/Bookmarks feature is completely client-side (localStorage) with no API equivalent. Agents cannot save, retrieve, or manage clips - creating an asymmetry where users can save research but agents cannot help them manage it.

**Why it matters:** Breaks the "agent-native" principle - anything a user can do, an agent should be able to do.

## Findings

**Location:** `web/app/page.tsx:165-188` (state), lines 271-362 (operations), lines 926-1029 (UI)

```typescript
// Clips are purely localStorage
useEffect(() => {
  const savedClips = localStorage.getItem('autography-clips')
  if (savedClips) {
    setClips(JSON.parse(savedClips))
  }
  setClipsLoaded(true)
}, [])

useEffect(() => {
  if (clipsLoaded) {
    localStorage.setItem('autography-clips', JSON.stringify(clips))
  }
}, [clips, clipsLoaded])
```

**Agent capability gaps:**
- Cannot save interesting passages
- Cannot retrieve previously saved clips
- Cannot help users organize research
- Cannot build workflows involving bookmarks

## Proposed Solutions

### Solution A: Add Server-Side Clips API (Recommended if clips are valuable)

Add API endpoints for clip CRUD:
- `POST /api/clips` - Create a clip
- `GET /api/clips` - List clips
- `DELETE /api/clips/:id` - Remove a clip
- `POST /api/clips/export` - Export clips

Would require session/identity management since clips are currently anonymous.

**Pros:** Full agent-native support, clips persist across devices
**Cons:** Requires backend changes, identity management
**Effort:** Large
**Risk:** Medium

### Solution B: Remove Clips Feature (Recommended if clips aren't used)

If analytics show clips aren't being used, removing the feature simplifies the codebase significantly (~200 LOC).

**Pros:** Simpler codebase, no agent-native gap
**Cons:** Loses feature for any users who do use it
**Effort:** Small
**Risk:** Low

## Technical Details

**Affected files:**
- `api/routers/` (new clips router)
- `web/app/page.tsx` (update to use API)
- `web/lib/api.ts` (add clips functions)

## Acceptance Criteria

- [ ] Agents can save clips via API
- [ ] Agents can list clips via API
- [ ] Agents can delete clips via API
- [ ] OR clips feature removed if not valuable

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-30 | Created from code review | Agent-native reviewer identified localStorage-only limitation |

## Resources

- Agent-native review findings
