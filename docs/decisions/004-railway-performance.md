# ADR-004: Railway Performance Optimization

**Date:** 2026-01-23
**Status:** Accepted
**Deciders:** Blake

## Context

Railway hobby tier services sleep after inactivity, causing cold starts of 10-30 seconds on first request. This creates poor UX for users hitting the API after idle periods.

## Decision

**Use free uptime monitoring to keep the service warm.**

Configure a free service (UptimeRobot or cron-job.org) to ping `https://autography-production.up.railway.app/health` every 5 minutes.

## Alternatives Considered

### 1. Upgrade Railway Plan (~$20+/mo)
**Deferred.**
- More resources and "always on" option
- Overkill for current traffic levels
- Will revisit if we need more CPU/RAM

### 2. Accept Cold Starts
**Rejected.**
- 10-30 second delays unacceptable for production UX
- Users will think the app is broken

### 3. Move to Always-On Platform (Render, Fly.io)
**Deferred.**
- Similar costs to Railway Pro
- Migration overhead not justified yet

## Implementation

1. Sign up at https://uptimerobot.com (free tier)
2. Add monitor: `https://autography-production.up.railway.app/health`
3. Set interval: 5 minutes
4. Enable alerts for downtime

## Consequences

### Positive
- Zero cost
- Eliminates cold starts for 90%+ of requests
- Provides uptime monitoring as bonus

### Negative
- Service runs continuously (minimal cost impact on hobby tier)
- Still one cold start if service crashes

## Scaling Path

When traffic grows:
1. Upgrade to Railway Pro for dedicated resources
2. Add horizontal scaling with multiple replicas
3. Consider edge caching for static responses
