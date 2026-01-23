# Claude Code Instructions

## Git Commits

- **Never add `Co-Authored-By: Claude` to commit messages** - all commits should appear as solely from the user

## Deployment

### Railway (Backend API)

- **Port: Always use 8080** - Railway injects `PORT=8080` environment variable
- Never hardcode port 8000 or other values in Dockerfile
- Use `${PORT:-8080}` for default fallback
- Public networking target port in Railway dashboard MUST be 8080
- If healthcheck passes but external requests return 502: check target port setting

### Vercel (Frontend)

- Root directory: `web/`
- Environment variable: `BACKEND_URL=https://autography-production.up.railway.app`
- **DO NOT set `NEXT_PUBLIC_API_URL`** - it causes CORS errors by bypassing the proxy
- The frontend proxies API calls through Next.js API routes to the Railway backend
- Set env var in Vercel Dashboard → Settings → Environment Variables (not in .env files)
- After changing env vars, push a new commit to trigger fresh build (redeploy from cache won't work for `NEXT_PUBLIC_*` vars)

### Data Storage

- ChromaDB version must match between local and deployed (currently 1.4.1)
- Data files hosted on GitHub Releases, downloaded during Docker build
- See ADR-003 for full data storage strategy

### Performance

- Use uptime monitoring (UptimeRobot) to ping `/health` every 5 min to prevent cold starts
- Claude model: `claude-sonnet-4-5-20250929`
- See ADR-004 for performance optimization details

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| 502 after healthcheck passes | Wrong target port | Set Railway public networking port to 8080 |
| CORS errors in browser | `NEXT_PUBLIC_API_URL` set | Remove it, only use `BACKEND_URL` |
| ChromaDB KeyError `_type` | Version mismatch | Match chromadb version in requirements.txt to local |
| Slow first request | Cold start | Set up uptime ping or upgrade Railway |
