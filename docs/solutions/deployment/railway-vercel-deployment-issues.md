# Railway + Vercel Deployment Issues

---
category: deployment
tags: [railway, vercel, cors, cold-start, next.js, fastapi]
severity: high
components: [api, web]
date_resolved: 2026-01-22
---

## Overview

Comprehensive documentation of issues encountered deploying Autography (Next.js frontend on Vercel + FastAPI backend on Railway) and their solutions.

## Issue 1: Railway 502 After Healthcheck Passes

### Symptom
- Healthcheck passes successfully
- Subsequent requests return 502 Bad Gateway
- Logs show the app is running fine

### Root Cause
Railway injects `PORT=8080` at runtime, but the public networking target port was configured to 8000.

### Solution
In Railway dashboard: Settings → Networking → Public Networking → Set target port to **8080**.

### Prevention
- Always check Railway's injected PORT environment variable
- Don't hardcode ports in Railway deployments
- Add to deployment checklist: verify target port matches runtime PORT

---

## Issue 2: CORS Errors in Browser

### Symptom
```
Access to fetch at 'https://autography-production.up.railway.app/api/search'
from origin 'https://autography-one.vercel.app' has been blocked by CORS policy
```

### Root Cause
`NEXT_PUBLIC_API_URL` was set in Vercel, causing the browser to make direct cross-origin requests to Railway instead of using the Next.js API proxy.

### Solution
1. Remove `NEXT_PUBLIC_API_URL` from Vercel environment variables
2. Only use `BACKEND_URL` (server-side only, used by API routes)
3. Trigger a **fresh build** (not just redeploy)

```typescript
// web/lib/api.ts - Correct pattern
const API_BASE = '/api'  // Always use relative path to Next.js proxy

// web/app/api/search/route.ts - Proxy to backend
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
```

### Key Insight
`NEXT_PUBLIC_*` variables are embedded at **build time**. A redeploy from cache won't clear them. You must trigger a fresh build (e.g., push an empty commit).

---

## Issue 3: Build Cache Retains Old Environment Variables

### Symptom
After removing `NEXT_PUBLIC_API_URL` and redeploying, the old value persists.

### Root Cause
Vercel's "Redeploy" uses cached build artifacts. `NEXT_PUBLIC_*` vars are baked into the JavaScript bundle at build time.

### Solution
Push any commit to trigger a fresh build:
```bash
git commit --allow-empty -m "chore: trigger fresh vercel build"
git push
```

### Prevention
- Understand that `NEXT_PUBLIC_*` = build-time embedding
- For environment variable changes, always trigger fresh builds
- Consider using runtime configuration for frequently-changed values

---

## Issue 4: ChromaDB Version Mismatch (KeyError `_type`)

### Symptom
```
KeyError: '_type'
```
When loading ChromaDB database on Railway.

### Root Cause
ChromaDB database was created with a different version than what's installed in the Docker image.

### Solution
Match the chromadb version in `requirements.txt` to the version used locally:
```
chromadb==1.4.1
```

### Prevention
- Pin exact versions for data-format-sensitive dependencies
- Include ChromaDB version in database metadata
- Test with production dependencies locally before deploying

---

## Issue 5: Slow First Request (Cold Start)

### Symptom
First request after idle period takes 10-30 seconds.

### Root Cause
Railway hobby tier services sleep after inactivity to save resources.

### Solution
Set up a keepalive ping using Vercel Cron:

```typescript
// web/app/api/cron/keepalive/route.ts
import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      headers: { 'User-Agent': 'Vercel-Cron-Keepalive' },
    })
    const data = await res.json()
    return NextResponse.json({
      status: 'ok',
      backend: data,
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    }, { status: 500 })
  }
}
```

```json
// web/vercel.json
{
  "crons": [
    {
      "path": "/api/cron/keepalive",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

### Alternatives
- Upgrade to Railway Pro (~$20/mo) for always-on
- Use external uptime monitoring (UptimeRobot, cron-job.org)

---

## Issue 6: UI Breakpoint Issues (Missing Sidebar)

### Symptom
Sources sidebar doesn't appear on laptop screens.

### Root Cause
Sidebar was set to show at `xl:` breakpoint (1280px), which is larger than many laptop screens.

### Solution
Change from `xl:` to `lg:` breakpoint (1024px):

```tsx
// Before
<div className="hidden xl:block ...">

// After
<div className="hidden lg:block ...">
```

### Prevention
- Test responsive layouts at common breakpoints (1024px, 1280px, 1440px)
- Consider mobile-first design with progressive enhancement
- Use browser DevTools device emulation during development

---

## Deployment Checklist

Use this checklist for future Railway + Vercel deployments:

### Pre-Deployment
- [ ] Pin all data-format-sensitive dependency versions (ChromaDB, etc.)
- [ ] Test locally with production dependencies
- [ ] Verify CORS configuration allows Vercel domain
- [ ] Confirm API proxy routes are set up (no NEXT_PUBLIC_API_URL)

### Railway Configuration
- [ ] Set target port to 8080 (matches Railway's injected PORT)
- [ ] Configure health check endpoint
- [ ] Set all required environment variables
- [ ] Attach persistent volume if needed

### Vercel Configuration
- [ ] Set BACKEND_URL (server-side only)
- [ ] Do NOT set NEXT_PUBLIC_API_URL
- [ ] Configure cron jobs for keepalive if using hobby tier
- [ ] Trigger fresh build after env var changes

### Post-Deployment Verification
- [ ] Test health endpoint directly
- [ ] Test search through Vercel proxy
- [ ] Verify no CORS errors in browser console
- [ ] Check responsive layout at multiple breakpoints
- [ ] Confirm cold start mitigation is working

---

## Related Documentation

- [ADR-001: Deployment Architecture](/docs/decisions/001-deployment-architecture.md)
- [ADR-004: Railway Performance Optimization](/docs/decisions/004-railway-performance.md)
- [CLAUDE.md - Common Issues Table](/CLAUDE.md#common-issues)

## References

- [Vercel Cron Jobs Documentation](https://vercel.com/docs/cron-jobs)
- [Railway Port Configuration](https://docs.railway.app/reference/variables#port)
- [Next.js Environment Variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
