---
status: pending
priority: p3
issue_id: "011"
tags: [code-review, bug, backend]
dependencies: []
---

# Buggy Default Follow-up Questions

## Problem Statement

The default follow-up generation creates malformed questions due to incorrect string handling.

## Findings

- **Location**: `api/routers/chat.py` lines 230-235
- **Evidence**:
  ```python
  follow_ups = [
      f"What else do these sources say about {chat_request.question.split()[0:3]}?",
      # ...
  ]
  ```
- **Bug**: `question.split()[0:3]` returns a list, which when formatted produces:
  ```
  "What else do these sources say about ['What', 'makes', 'a']?"
  ```
- **Expected**:
  ```
  "What else do these sources say about What makes a?"
  ```

## Proposed Solutions

### Option 1: Fix String Formatting (Recommended)
```python
f"What else do these sources say about {' '.join(chat_request.question.split()[:3])}?"
```
- **Pros**: Quick fix
- **Cons**: None
- **Effort**: Trivial
- **Risk**: None

### Option 2: Remove Default Follow-ups
- **Pros**: Let LLM generate all follow-ups
- **Cons**: Fallback lost
- **Effort**: Trivial
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `api/routers/chat.py`
- **Line**: 232

## Acceptance Criteria

- [ ] Default follow-ups are grammatically correct
- [ ] No Python list repr in user-facing text

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Test edge cases |

## Resources

- Simplicity review agent: a3d7cad
