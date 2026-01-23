# ADR-001: Deployment Architecture

**Date:** 2026-01-22
**Status:** Accepted
**Deciders:** Blake

## Context

Autography is a RAG-based PM knowledge base with:
- **Frontend:** Next.js 15 with React 19, TailwindCSS
- **Backend:** FastAPI with hybrid search (ChromaDB + BM25)
- **AI:** Claude for response generation via streaming SSE

We needed to deploy this to production with a budget of ~$5-20/month.

## Decision

**Split deployment architecture:**

```
┌─────────────────────┐          ┌─────────────────────┐
│   Vercel (free)     │  HTTPS   │   Railway (~$5/mo)  │
│                     │─────────▶│                     │
│   Next.js frontend  │          │   FastAPI backend   │
│                     │          │   ChromaDB + BM25   │
└─────────────────────┘          └─────────────────────┘
```

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend (Next.js) | Vercel | Free |
| Backend (FastAPI + ML) | Railway | ~$5-20/mo |
| Domain | autography.dev | $20.99/yr |

## Alternatives Considered

### 1. All on Vercel
**Rejected.** Vercel serverless has a 250MB limit. Our backend dependencies exceed this:
- ChromaDB: ~192MB
- BM25 index: ~71MB
- SentenceTransformers: ~100MB+

### 2. All on Railway
**Considered but not chosen.** Would work, but Vercel's free tier for Next.js is better optimized for frontend delivery (CDN, edge functions).

### 3. Fly.io instead of Railway
**Considered.** Fly.io offers similar pricing and multi-region deployment. Chose Railway for simpler GitHub integration and built-in volumes.

### 4. Managed vector DB (Qdrant Cloud / Pinecone)
**Deferred.** For current scale (~700 docs), local ChromaDB is sufficient. Will revisit at 10x scale.

## Consequences

### Positive
- Cost-effective (~$5-25/month total)
- Each platform optimized for its workload
- Simple deployment via GitHub integration
- Scales independently

### Negative
- Two platforms to manage
- Need CORS configuration between services
- Cold starts possible on Railway (mitigated by health checks)

### Risks
- Railway pricing could change
- Need to migrate if data exceeds Railway limits

## Implementation Details

**Railway:**
- Dockerfile in `api/Dockerfile`
- Config in `railway.toml`
- Volumes for persistent data
- Environment variables: `ANTHROPIC_API_KEY`, `CORS_ORIGINS`

**Vercel:**
- Root directory: `web/`
- Framework preset: Next.js
- Environment variable: `NEXT_PUBLIC_API_URL`

**Git LFS:**
- Tracking `chroma_db/chroma.sqlite3` (247MB)
- Tracking `bm25_index.pkl` (71MB)

## Scaling Path

| Scale | Solution | Cost |
|-------|----------|------|
| Current (~700 docs) | Railway + Vercel | ~$5-25/mo |
| 10x (~7k docs) | + Qdrant Cloud + Typesense | ~$50-80/mo |
| 100x (~70k docs) | Supabase pgvector + OpenAI embeddings | ~$100-200/mo |

## Related Decisions

- ADR-002: Domain Selection (autography.dev)
