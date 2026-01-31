---
status: pending
priority: p3
issue_id: "029"
tags: [code-review, quality]
dependencies: []
---

# BACKEND_URL Defined in 6 Separate Files

## Problem Statement

The same BACKEND_URL constant is defined identically in 6 different API route files, violating DRY principle.

## Findings

**Locations:**
- `web/app/api/chat/route.ts:3`
- `web/app/api/chat/stream/route.ts:3`
- `web/app/api/search/route.ts:3`
- `web/app/api/sources/route.ts:3`
- `web/app/api/suggestions/route.ts:3`
- `web/app/api/cron/keepalive/route.ts:3`

```typescript
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
```

## Proposed Solutions

### Solution A: Extract to Config Module (Recommended)

Create `web/lib/config.ts`:

```typescript
export const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
```

Import in each route:
```typescript
import { BACKEND_URL } from '@/lib/config'
```

**Pros:** Single source of truth, easier to change
**Cons:** One more import
**Effort:** Small
**Risk:** None

## Technical Details

**Affected files:**
- `web/lib/config.ts` (new)
- All 6 API route files

## Acceptance Criteria

- [ ] BACKEND_URL defined in single location
- [ ] All API routes import from config
- [ ] Default value only in one place

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-30 | Created from code review | Pattern recognition found 6 duplications |

## Resources

- Pattern recognition review findings
