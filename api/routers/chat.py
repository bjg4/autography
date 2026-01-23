"""
Chat router for RAG-powered Q&A with citations.

This is the core Autography experience - synthesized answers with evidence.
"""

import os
from typing import Optional

import anthropic
from anthropic import AsyncAnthropic
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from routers.search import get_search_engine

router = APIRouter(prefix="/api", tags=["chat"])

# Rate limiter - 10 requests per minute for expensive chat endpoints
limiter = Limiter(key_func=get_remote_address)

# Initialize async Anthropic client (doesn't block FastAPI event loop)
client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You synthesize product management wisdom from books, essays, and practitioner conversations.

CRITICAL: Your first sentence must be substantive insight, not meta-commentary.

BANNED OPENINGS (never use these patterns):
- "Based on the sources..."
- "Based on the provided..."
- "According to the sources..."
- "The sources suggest..."
- "What makes a great X comes down to..."
- "There are several key factors..."
- "Great question!"
- Any sentence that describes what you're about to do

GOOD OPENINGS (use patterns like these):
- "The highest-performing teams share one trait: they fight about the right things. [1]"
- "Teresa Torres and Marty Cagan actually disagree on this—and the tension is instructive."
- "Forget the triad. The best teams are quads now, with data as the fourth pillar. [2]"
- "There's no single answer here, but John Cutler's research points to something unexpected..."
- Start with a specific claim, tension, or insight—then support it.

HOW TO RESPOND:
- Lead with the most interesting insight, not a summary structure
- Cite [1], [2] etc. inline as you reference specific sources
- Surface disagreements between authors—don't flatten them
- Match response length to question complexity (short questions = short answers)

FOLLOW-UP FORMAT (required at end):
After your response, add exactly this format:
---
- First follow-up question?
- Second follow-up question?
- Third follow-up question?

Do NOT write "Follow-up threads:" or any header. Just the separator, then bullet points with questions.

Your sources include Marty Cagan, Teresa Torres, John Cutler, Ryan Singer, and others who often disagree. That disagreement is valuable—show it."""


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    question: str
    answer: str


class ChatRequest(BaseModel):
    """Chat request body."""
    question: str = Field(..., min_length=1, description="User's question")
    n_sources: int = Field(default=8, ge=1, le=20, description="Number of sources to retrieve")
    source_types: Optional[list[str]] = Field(default=None, description="Filter by source types")
    authors: Optional[list[str]] = Field(default=None, description="Filter by authors")
    history: Optional[list[ConversationTurn]] = Field(default=None, description="Previous conversation turns for context")


class Citation(BaseModel):
    """A citation from a source."""
    index: int
    title: str
    author: str
    source_type: str
    content: str
    metadata: dict


class ChatResponse(BaseModel):
    """Chat response with answer and citations."""
    answer: str
    citations: list[Citation]
    follow_ups: list[str]


def format_sources_for_context(results: list[dict]) -> tuple[str, list[Citation]]:
    """Format retrieved sources for the LLM context."""
    context_parts = []
    citations = []

    for i, result in enumerate(results, 1):
        meta = result['metadata']
        content = result['content']

        # Build context string
        source_info = f"[{i}] {meta.get('title', 'Untitled')} by {meta.get('author', 'Unknown')}"
        if meta.get('source_type') == 'book_chapter' and meta.get('book_title'):
            source_info += f" (from {meta['book_title']})"

        context_parts.append(f"{source_info}\n{content}\n")

        # Build citation object - try multiple title fields
        title = meta.get('title') or meta.get('book_title') or meta.get('episode_title') or 'Untitled'

        citations.append(Citation(
            index=i,
            title=title,
            author=meta.get('author', 'Unknown'),
            source_type=meta.get('source_type', 'unknown'),
            content=content[:1500] + ('...' if len(content) > 1500 else ''),
            metadata=meta
        ))

    return "\n---\n".join(context_parts), citations


def extract_follow_ups(answer: str) -> tuple[str, list[str]]:
    """Extract follow-up questions from the answer."""
    follow_ups = []

    # Try new format first (--- separator)
    if "\n---" in answer:
        parts = answer.split("\n---")
        main_answer = parts[0].strip()
        follow_up_text = parts[1].strip() if len(parts) > 1 else ""
    # Fall back to old format
    elif "Follow-up questions:" in answer:
        parts = answer.split("Follow-up questions:")
        main_answer = parts[0].strip()
        follow_up_text = parts[1].strip() if len(parts) > 1 else ""
    else:
        return answer, follow_ups

    for line in follow_up_text.split('\n'):
        line = line.strip()
        if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
            clean = line.lstrip('-•0123456789. ').strip()
            if clean and '?' in clean:
                follow_ups.append(clean)

    return main_answer, follow_ups[:3]


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(chat_request: ChatRequest, request: Request):
    """Answer a question using RAG with citations."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured. Set it in your environment."
        )

    # 1. Retrieve relevant sources
    engine = get_search_engine()
    results = engine.search(
        query=chat_request.question,
        n_results=chat_request.n_sources,
        source_types=chat_request.source_types,
        authors=chat_request.authors,
        mode="hybrid"
    )

    if not results:
        return ChatResponse(
            answer="I couldn't find any relevant sources in the knowledge base for your question. Try rephrasing or asking about a different PM topic.",
            citations=[],
            follow_ups=[
                "What topics are covered in this knowledge base?",
                "Can you help me understand product discovery?",
                "What does the research say about team structure?"
            ]
        )

    # 2. Format sources for context
    context, citations = format_sources_for_context(results)

    # Log token estimate for debugging
    total_words = sum(len(r['content'].split()) for r in results)
    print(f"[Chat] Retrieved {len(results)} sources, ~{total_words} words (~{int(total_words * 1.3)} tokens)")

    # 3. Build messages with conversation history
    messages = []

    # Add previous conversation turns if present (limit to last 3 for token efficiency)
    if chat_request.history:
        recent_history = chat_request.history[-3:]  # Keep last 3 turns max
        for turn in recent_history:
            messages.append({"role": "user", "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})

    # Add current question with retrieved context
    user_message = f"""{chat_request.question}

Here's what I found in the knowledge base:

{context}"""
    messages.append({"role": "user", "content": user_message})

    # 4. Call Claude to synthesize answer (async - doesn't block event loop)
    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        answer_text = response.content[0].text
    except anthropic.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a minute and try again."
        )
    except anthropic.APIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {str(e)}"
        )

    # 4. Extract follow-ups and clean answer
    clean_answer, follow_ups = extract_follow_ups(answer_text)

    # Default follow-ups if none extracted
    if not follow_ups:
        follow_ups = [
            f"What else do these sources say about {chat_request.question.split()[0:3]}?",
            "Are there any contrasting viewpoints on this topic?",
            "How do I apply this in practice?"
        ]

    return ChatResponse(
        answer=clean_answer,
        citations=citations,
        follow_ups=follow_ups
    )


@router.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(chat_request: ChatRequest, request: Request):
    """Stream a chat response for real-time display."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured"
        )

    engine = get_search_engine()
    results = engine.search(
        query=chat_request.question,
        n_results=chat_request.n_sources,
        source_types=chat_request.source_types,
        authors=chat_request.authors,
        mode="hybrid"
    )

    context, citations = format_sources_for_context(results)

    # Build messages with conversation history (same as non-streaming endpoint)
    messages = []

    # Add previous conversation turns if present (limit to last 3 for token efficiency)
    if chat_request.history:
        recent_history = chat_request.history[-3:]
        for turn in recent_history:
            messages.append({"role": "user", "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})

    # Add current question with retrieved context
    user_message = f"""{chat_request.question}

Here's what I found in the knowledge base:

{context}"""
    messages.append({"role": "user", "content": user_message})

    async def generate():
        import json

        # First, send citations
        yield f"data: {json.dumps({'type': 'citations', 'data': [c.model_dump() for c in citations]})}\n\n"

        # Then stream the answer (async - doesn't block event loop)
        async with client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'token', 'data': text})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
