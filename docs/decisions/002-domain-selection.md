# ADR-002: Domain Selection

**Date:** 2026-01-22
**Status:** Accepted
**Deciders:** Blake

## Context

Needed a domain for the Autography PM knowledge base. Budget: max $40.

## Decision

**Selected:** `autography.dev` at $20.99/year

## Alternatives Considered

| Domain | Price | Notes |
|--------|-------|-------|
| autography.dev | $20.99 | Professional, tech-credible |
| autography.io | N/A | Not available |
| autography.me | $8.99 | Too personal |
| autography.site | $2.99 | Cheap but less professional |
| autography.tech | $4.99 | High renewal ($63.99) |
| autography.cloud | $3.99 | Decent but less memorable |
| autography.org | $5,655 | Premium pricing, rejected |

## Why .dev

1. **Professional and tech-credible** — recognized TLD for developer/tech products
2. **Memorable** — short, clean
3. **Stable pricing** — renewal same tier as initial purchase
4. **HTTPS required** — .dev is HSTS preloaded (not a problem since Vercel/Railway provide SSL automatically)

## Consequences

- Annual renewal: ~$21
- Requires HTTPS (automatically handled by hosting platforms)
- Good SEO for tech/developer audience

## DNS Configuration

| Record | Type | Value |
|--------|------|-------|
| @ | A/CNAME | Vercel (frontend) |
| api | CNAME | Railway URL |

Final URLs:
- Frontend: `https://autography.dev`
- Backend: `https://api.autography.dev` (or Railway default URL)
