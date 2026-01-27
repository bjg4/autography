---
status: pending
priority: p1
issue_id: "003"
tags: [code-review, security, validation]
dependencies: []
---

# Missing Input Length Validation - Token Abuse & DoS Risk

## Problem Statement

The `ChatRequest` model lacks maximum length constraints on questions and conversation history. An attacker could send extremely long inputs causing high API costs, memory exhaustion, or denial of service.

## Findings

- **Location**: `api/routers/chat.py` lines 59-71
- **Evidence**:
  ```python
  class ConversationTurn(BaseModel):
      question: str  # No max_length
      answer: str    # No max_length

  class ChatRequest(BaseModel):
      question: str = Field(..., min_length=1)  # No max_length!
      history: Optional[list[ConversationTurn]]  # No max_items!
  ```
- **Impact**:
  - Megabyte-sized questions = huge Anthropic API costs
  - Unbounded history = memory exhaustion
  - Slow responses = DoS other users

## Proposed Solutions

### Option 1: Add Pydantic Constraints (Recommended)
```python
class ConversationTurn(BaseModel):
    question: str = Field(..., max_length=10000)
    answer: str = Field(..., max_length=50000)

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000)
    history: Optional[list[ConversationTurn]] = Field(default=None, max_items=10)
```
- **Pros**: Simple, catches issues at validation layer
- **Cons**: None significant
- **Effort**: Small
- **Risk**: Low

## Recommended Action

_To be filled during triage_

## Technical Details

- **Affected Files**: `api/routers/chat.py`
- **Components**: ChatRequest, ConversationTurn models

## Acceptance Criteria

- [ ] Questions limited to 10,000 characters
- [ ] Answers in history limited to 50,000 characters
- [ ] History limited to 10 turns maximum
- [ ] API returns 422 with clear error for oversized inputs

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-22 | Created from code review | Always validate input bounds |

## Resources

- Pydantic Field docs: https://docs.pydantic.dev/latest/concepts/fields/
- Security review agent: a316af9
