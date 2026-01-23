# Deployment Checklist

Prevention strategies and best practices based on Railway + Vercel deployment issues.

## Pre-Deployment Validation

### 1. Port Configuration

- [ ] **Never hardcode ports** - always use environment variable
  ```python
  # Good
  CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

  # Bad
  CMD uvicorn main:app --host 0.0.0.0 --port 8000
  ```

- [ ] **Railway uses PORT=8080 by default** - don't fight it
  ```dockerfile
  EXPOSE 8080
  CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
  ```

- [ ] **Target port in Railway dashboard matches app listening port**
  - Navigate to: Service Settings → Public Networking → Target Port
  - Set to: `8080`
  - **Symptom if wrong:** Healthcheck passes but external requests return 502 with `X-Railway-Fallback: true`

### 2. Dependency Versioning

- [ ] **Pin exact versions for all packages**
  ```txt
  # Good - requirements.txt
  chromadb==1.4.1
  sentence-transformers==3.3.1

  # Bad
  chromadb>=1.0
  sentence-transformers
  ```

- [ ] **Verify local and deployed versions match**
  ```bash
  # Local
  pip freeze | grep chromadb

  # Deployed (check Railway logs)
  # Should show same version during pip install
  ```

- [ ] **Document minimum versions in README or requirements**
  - ChromaDB: Known breaking changes between major versions
  - PyTorch: CPU vs GPU builds have different sizes

- [ ] **Test with exact deployed versions locally**
  ```bash
  pip install -r requirements.txt --no-deps
  ```

### 3. Environment Variables

#### Vercel (Frontend)

- [ ] **Never set NEXT_PUBLIC_* to external URLs** (causes CORS in browser)
  ```bash
  # Bad - causes CORS errors
  NEXT_PUBLIC_API_URL=https://api.railway.app

  # Good - use server-side proxy
  BACKEND_URL=https://api.railway.app  # Server-only
  ```

- [ ] **Use Next.js rewrites for API proxy** (avoids CORS entirely)
  ```javascript
  // next.config.js
  module.exports = {
    async rewrites() {
      return [{
        source: '/api/:path*',
        destination: `${process.env.BACKEND_URL}/api/:path*`,
      }]
    }
  }
  ```

- [ ] **Frontend env vars reference:**
  | Variable | Where to Set | Exposed to Browser |
  |----------|--------------|-------------------|
  | `BACKEND_URL` | Vercel (server) | No |
  | `NEXT_PUBLIC_*` | Vercel | Yes (avoid for APIs) |

#### Railway (Backend)

- [ ] **Required environment variables set:**
  - `ANTHROPIC_API_KEY` - for Claude API
  - `CORS_ORIGINS` - allowed frontend origins
  - `PORT` - Railway sets automatically (8080)

- [ ] **CORS configured properly**
  ```python
  # main.py
  origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
  app.add_middleware(
      CORSMiddleware,
      allow_origins=origins,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### 4. Docker Optimization

- [ ] **Use CPU-only PyTorch** (saves ~1.5GB)
  ```dockerfile
  # Good - CPU only (~200MB)
  RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

  # Bad - Full PyTorch (~2GB)
  RUN pip install torch
  ```

- [ ] **Pre-cache ML models in build** (avoids runtime downloads)
  ```dockerfile
  # Pre-download sentence transformer
  RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
  ```

- [ ] **Clean up apt cache**
  ```dockerfile
  RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
  ```

- [ ] **Use --no-cache-dir for pip**
  ```dockerfile
  RUN pip install --no-cache-dir -r requirements.txt
  ```

- [ ] **Order Dockerfile layers** (most stable first)
  1. Base image and system deps
  2. Python packages (requirements.txt)
  3. Pre-cache models
  4. Application code (changes most often)

### 5. Data Storage

- [ ] **Don't rely on Git LFS for Railway deployments**
  - Railway doesn't automatically pull LFS files
  - Builds fail with pointer files instead of actual data

- [ ] **Use GitHub Releases for deployment data**
  ```dockerfile
  # Download data from GitHub release
  RUN curl -L https://github.com/USER/REPO/releases/download/v1.0.0/data.tar.gz -o data.tar.gz \
      && tar -xzf data.tar.gz \
      && rm data.tar.gz
  ```

- [ ] **Create a GitHub release with data artifacts**
  ```bash
  # Package data
  tar -czvf data.tar.gz chroma_db/ bm25_index.pkl

  # Create release (use GitHub UI or gh CLI)
  gh release create v1.0.0 data.tar.gz --title "Data Release"
  ```

- [ ] **Document data dependencies**
  | File | Size | Source |
  |------|------|--------|
  | `chroma_db/` | 247MB | GitHub Release |
  | `bm25_index.pkl` | 71MB | GitHub Release |

---

## Railway Deployment Checklist

### Initial Setup

- [ ] Connect GitHub repository
- [ ] Set root directory if needed (for monorepos)
- [ ] Configure Dockerfile path in `railway.toml`

### Configuration

- [ ] **railway.toml exists with correct settings:**
  ```toml
  [build]
  dockerfilePath = "api/Dockerfile"

  [deploy]
  healthcheckPath = "/health"
  healthcheckTimeout = 600
  restartPolicyType = "ON_FAILURE"
  restartPolicyMaxRetries = 3
  ```

- [ ] **Set environment variables** (Settings → Variables)
- [ ] **Set target port to 8080** (Settings → Public Networking)
- [ ] **Enable public networking** (generate domain)

### Validation

- [ ] Check build logs for errors
- [ ] Verify health endpoint responds: `curl https://your-app.railway.app/health`
- [ ] Test actual API endpoints
- [ ] Check no `X-Railway-Fallback: true` header in responses

---

## Vercel Deployment Checklist

### Initial Setup

- [ ] Connect GitHub repository
- [ ] Set root directory to `web/` (for monorepos)
- [ ] Framework preset: Next.js

### Configuration

- [ ] **Set environment variables:**
  - `BACKEND_URL` = Railway app URL

- [ ] **vercel.json if needed** (cron jobs, etc.)
  ```json
  {
    "crons": [{
      "path": "/api/cron/keepalive",
      "schedule": "*/5 * * * *"
    }]
  }
  ```

### Validation

- [ ] Check deployment logs for build errors
- [ ] Test frontend loads
- [ ] Test API calls work through proxy
- [ ] No CORS errors in browser console

---

## Post-Deployment Monitoring

### Set Up Uptime Monitoring (Free)

- [ ] **Configure UptimeRobot or similar:**
  - URL: `https://your-app.railway.app/health`
  - Interval: 5 minutes
  - Alert on downtime

- [ ] **Purpose:** Prevents Railway hobby tier cold starts

### Verify Everything Works

- [ ] Frontend loads without errors
- [ ] API endpoints respond
- [ ] Streaming/SSE works
- [ ] No CORS errors in browser console
- [ ] Mobile responsive (if applicable)

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 502 with `X-Railway-Fallback: true` | Target port mismatch | Set target port to 8080 in Railway dashboard |
| CORS errors in browser | `NEXT_PUBLIC_*` pointing to external URL | Use server-side rewrites instead |
| Cold start delays | Railway hobby tier sleep | Set up UptimeRobot ping every 5 min |
| Build fails with "file not found" | Git LFS not pulled | Use GitHub Releases instead |
| Docker image too large | Full PyTorch installed | Use CPU-only: `--index-url https://download.pytorch.org/whl/cpu` |
| Model download on every startup | Model not cached in build | Add `RUN python -c "..."` to Dockerfile |
| Version mismatch errors | Unpinned dependencies | Pin exact versions in requirements.txt |

---

## Version Requirements

**Current tested versions (2026-01-22):**

```txt
# Python dependencies (api/requirements.txt)
fastapi==0.115.0
uvicorn[standard]==0.30.6
chromadb==1.4.1
sentence-transformers==3.3.1
rank-bm25==0.2.2
pydantic==2.10.3
anthropic==0.42.0
sse-starlette==2.1.3
```

```json
// Node.js dependencies (web/package.json)
"next": "15.x",
"react": "19.x"
```

---

## Related Documentation

- [ADR-001: Deployment Architecture](/docs/decisions/001-deployment-architecture.md)
- [ADR-003: Data Storage Strategy](/docs/decisions/003-data-storage-strategy.md)
- [ADR-004: Railway Performance](/docs/decisions/004-railway-performance.md)
