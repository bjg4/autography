# ADR-003: Data Storage Strategy

**Date:** 2026-01-22
**Status:** Accepted
**Deciders:** Blake

## Context

The application requires storage for:
- **Vector embeddings:** ~700 documents embedded with all-MiniLM-L6-v2
- **BM25 index:** Keyword search index
- **Total size:** ~340MB

Options ranged from committing to git, using managed services, or Railway volumes.

## Decision

**Commit data to Git with Git LFS, deploy via Docker image.**

```
Repository
├── chroma_db/
│   └── chroma.sqlite3  (247MB, tracked by LFS)
├── bm25_index.pkl      (71MB, tracked by LFS)
└── api/
    └── Dockerfile      (copies data into image)
```

## Alternatives Considered

### 1. Managed Vector DB (Qdrant Cloud, Pinecone)
**Deferred.**
- Adds cost (~$25-70/mo at scale)
- Adds complexity (API integration)
- Overkill for ~700 documents
- Will revisit at 10x scale

### 2. Railway Volumes Only
**Rejected.**
- Requires manual data upload
- Data not versioned with code
- Harder to reproduce deployments

### 3. Download data on startup
**Rejected.**
- Slow cold starts
- Requires separate storage (S3, etc.)
- More moving parts

### 4. Commit without LFS
**Rejected.**
- `chroma.sqlite3` at 247MB exceeds GitHub's 100MB file limit
- Would bloat git history

## Git LFS Configuration

```bash
# .gitattributes
chroma_db/chroma.sqlite3 filter=lfs diff=lfs merge=lfs -text
bm25_index.pkl filter=lfs diff=lfs merge=lfs -text
```

GitHub provides 1GB free LFS storage — sufficient for current needs.

## Consequences

### Positive
- Data versioned with code
- Reproducible deployments
- No external dependencies
- Simple Dockerfile

### Negative
- Large initial clone (~340MB)
- LFS adds slight complexity
- GitHub LFS has storage limits (1GB free, then $5/mo per 50GB)

## Scaling Path

When data grows significantly (10x+):

1. **Migrate to Qdrant Cloud** — managed vector DB with free tier
2. **Migrate to Typesense Cloud** — replace BM25 with better relevance
3. **Keep Railway** for FastAPI orchestration

This avoids premature optimization while maintaining a clear upgrade path.
