"""
Chat router for RAG-powered Q&A with citations.

This is the core Autography experience - synthesized answers with evidence.
"""

import os
from typing import Optional

import anthropic
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from routers.search import get_search_engine

router = APIRouter(prefix="/api", tags=["chat"])

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Autography, a warm and knowledgeable assistant helping users explore product management wisdom from trusted sources.

Your role is to synthesize insights from the provided source materials and give clear, actionable answers.

IMPORTANT RULES:
1. ALWAYS cite your sources using [1], [2], [3] notation when referencing information
2. Only use information from the provided sources - never make things up
3. If the sources don't contain relevant information, say so honestly
4. Be conversational but precise
5. After your answer, suggest 2-3 follow-up questions the user might want to explore

Format your response like this:
- Start with a direct answer to the question
- Support key points with citations [1], [2], etc.
- Keep it concise but complete
- End with "Follow-up questions:" section"""


class ChatRequest(BaseModel):
    """Chat request body."""
    question: str = Field(..., min_length=1, description="User's question")
    n_sources: int = Field(default=8, ge=1, le=20, description="Number of sources to retrieve")


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

    if "Follow-up questions:" in answer:
        parts = answer.split("Follow-up questions:")
        main_answer = parts[0].strip()
        follow_up_text = parts[1].strip() if len(parts) > 1 else ""

        for line in follow_up_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                # Clean up the line
                clean = line.lstrip('-•0123456789. ').strip()
                if clean and '?' in clean:
                    follow_ups.append(clean)

        return main_answer, follow_ups[:3]

    return answer, follow_ups


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
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
        query=request.question,
        n_results=request.n_sources,
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

    # 3. Call Claude to synthesize answer
    user_message = f"""Based on the following sources from the PM knowledge base, answer this question:

Question: {request.question}

Sources:
{context}

Remember to cite sources using [1], [2], etc. and end with follow-up questions."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    answer_text = response.content[0].text

    # 4. Extract follow-ups and clean answer
    clean_answer, follow_ups = extract_follow_ups(answer_text)

    # Default follow-ups if none extracted
    if not follow_ups:
        follow_ups = [
            f"What else do these sources say about {request.question.split()[0:3]}?",
            "Are there any contrasting viewpoints on this topic?",
            "How do I apply this in practice?"
        ]

    return ChatResponse(
        answer=clean_answer,
        citations=citations,
        follow_ups=follow_ups
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream a chat response for real-time display."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured"
        )

    engine = get_search_engine()
    results = engine.search(
        query=request.question,
        n_results=request.n_sources,
        mode="hybrid"
    )

    context, citations = format_sources_for_context(results)

    user_message = f"""Based on the following sources from the PM knowledge base, answer this question:

Question: {request.question}

Sources:
{context}

Remember to cite sources using [1], [2], etc. and end with follow-up questions."""

    async def generate():
        import json

        # First, send citations
        yield f"data: {json.dumps({'type': 'citations', 'data': [c.model_dump() for c in citations]})}\n\n"

        # Then stream the answer
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        ) as stream:
            for text in stream.text_stream:
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
