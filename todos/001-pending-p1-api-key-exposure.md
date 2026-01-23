---
status: pending
priority: p1
issue_id: "001"
tags: [code-review, security, critical]
dependencies: []
---

# API Key Exposure in .env File

## Problem Statement

The Anthropic API key is stored in plaintext in the `.env` file. While `.env` is gitignored, this key may have been exposed at some point and represents a significant security risk. An attacker with this key could make API calls at your expense.

## Findings

- **Location**: `/api/.env` line 1
- **Evidence**: File contains `ANTHROPIC_API_KEY=sk-ant-api03-...`
- **Severity**: CRITICAL - immediate action required

## Proposed Solutions

### Option 1: Rotate Key Immediately (Recommended)
- **Pros**: Immediately invalidates any leaked key
- **Cons**: Requires updating deployment environments
- **Effort**: Small
- **Risk**: Low

### Option 2: Move to Secrets Manager
- **Pros**: Best practice for production
- **Cons**: Requires infrastructure setup
- **Effort**: Medium
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `api/.env`, deployment configurations
- **Components**: FastAPI backend authentication

## Acceptance Criteria

- [ ] Anthropic API key has been rotated in the Anthropic console
- [ ] New key is stored in environment variables (not in files)
- [ ] Old key no longer works
- [ ] Application still functions correctly

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Found during security-sentinel review |

## Resources

- Anthropic Console: https://console.anthropic.com/
- Security review agent: a316af9
