import { NextRequest } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      return new Response(
        JSON.stringify({ detail: error.detail || `Backend error: ${response.statusText}` }),
        { status: response.status, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Stream the SSE response through
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error('Stream proxy error:', error)
    return new Response(
      JSON.stringify({ detail: 'Failed to connect to backend' }),
      { status: 502, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
