---
status: pending
priority: p1
issue_id: "013"
tags: [code-review, security, authentication]
dependencies: []
---

# Client-Side Password Gate Can Be Bypassed

## Problem Statement

The password gate (`PasswordGate.tsx`) is implemented entirely on the client-side with the password "AIA" hardcoded in the JavaScript source. This provides zero actual security - anyone can bypass it via browser console or by calling API endpoints directly.

## Findings

- **Location**: `web/components/PasswordGate.tsx` lines 5, 18-27
- **Evidence**:
  ```typescript
  const CORRECT_PASSWORD = 'AIA'  // Visible in source code

  const handleSubmit = (e: React.FormEvent) => {
    if (password.toUpperCase() === CORRECT_PASSWORD) {
      localStorage.setItem(STORAGE_KEY, 'granted')  // Client-side "auth"
      setAuthorized(true)
    }
  }
  ```
- **Bypass Methods**:
  1. View password in browser DevTools (Sources tab)
  2. Run `localStorage.setItem('autography_access', 'granted')` in console
  3. Call API endpoints directly (no auth required)

## Proposed Solutions

### Option 1: Accept as Soft Gate (Document Limitation)
- Keep current implementation but document it's not real security
- Add comment explaining it's UX friction only
- **Pros**: No work needed
- **Cons**: Creates false security impression
- **Effort**: Trivial
- **Risk**: Low (if documented)

### Option 2: Add API-Level Authentication
- Add Bearer token or API key authentication middleware
- Generate tokens on password validation
- **Pros**: Actual security
- **Cons**: More complexity, needs token management
- **Effort**: Medium
- **Risk**: Low

### Option 3: Remove Password Gate Entirely
- Delete `PasswordGate.tsx` and wrapper
- Rely on rate limiting for abuse protection
- **Pros**: Simpler, no false security
- **Cons**: No access control
- **Effort**: Small
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**:
  - `web/components/PasswordGate.tsx`
  - `web/app/layout.tsx`
  - `api/main.py` (if adding server auth)
- **Components**: PasswordGate, FastAPI middleware

## Acceptance Criteria

- [ ] Decision made: soft gate, real auth, or removal
- [ ] If keeping, add comment documenting it's not security
- [ ] If adding server auth, all /api endpoints require valid token
- [ ] If removing, PasswordGate component deleted

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-26 | Created from security review | Client-side auth is not auth |

## Resources

- Security review agent: acae90f
- Agent-native review agent: ac35e44
