---
status: pending
priority: p1
issue_id: "002"
tags: [code-review, security, high]
dependencies: []
---

# Unsafe Pickle Deserialization (RCE Risk)

## Problem Statement

The BM25 index is loaded using Python's `pickle.load()` which can execute arbitrary code during deserialization. While there's a SHA256 checksum validation mechanism, it only runs if a `.sha256` file exists - making it optional rather than mandatory.

## Findings

- **Location**: `api/routers/search.py` lines 90-116
- **Evidence**:
  ```python
  checksum_path = Path(bm25_path).with_suffix('.sha256')
  if checksum_path.exists():  # Optional check - should be mandatory
      # validation happens
  with open(bm25_path, 'rb') as f:
      cache = pickle.load(f)  # Unsafe
  ```
- **Severity**: HIGH - Remote Code Execution possible if index file is compromised

## Proposed Solutions

### Option 1: Make Checksum Mandatory (Recommended)
- **Pros**: Quick fix, maintains current architecture
- **Cons**: Requires generating checksum file
- **Effort**: Small
- **Risk**: Low

### Option 2: Migrate to Safer Serialization
- **Pros**: Eliminates pickle risk entirely
- **Cons**: Requires re-indexing, more complex migration
- **Effort**: Large
- **Risk**: Medium

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `api/routers/search.py`, `bm25_index.pkl`
- **Components**: HybridSearch class initialization

## Acceptance Criteria

- [ ] Checksum validation is mandatory (raises error if no checksum file)
- [ ] SHA256 checksum file exists alongside BM25 index
- [ ] Index loading fails gracefully with clear error if checksum mismatch

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Pickle is dangerous for untrusted data |

## Resources

- Python pickle security: https://docs.python.org/3/library/pickle.html#restricting-globals
- Security review agent: a316af9
