const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

export interface Citation {
  index: number
  title: string
  author: string
  source_type: string
  content: string
  metadata: Record<string, unknown>
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  follow_ups: string[]
}

export interface SourcesResponse {
  source_types: string[]
  authors: string[]
  stats: {
    total_documents: number
  }
}

export interface ConversationTurn {
  question: string
  answer: string
}

export interface ChatOptions {
  nSources?: number
  sourceTypes?: string[]
  authors?: string[]
  history?: ConversationTurn[]
}

export async function askQuestion(
  question: string,
  options: ChatOptions = {}
): Promise<ChatResponse> {
  const { nSources = 8, sourceTypes, authors, history } = options

  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      n_sources: nSources,
      source_types: sourceTypes?.length ? sourceTypes : undefined,
      authors: authors?.length ? authors : undefined,
      history: history?.length ? history : undefined,
    }),
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `Request failed: ${res.statusText}`)
  }

  return res.json()
}

export async function getSources(): Promise<SourcesResponse> {
  const res = await fetch(`${API_URL}/api/sources`)

  if (!res.ok) {
    throw new Error(`Failed to get sources: ${res.statusText}`)
  }

  return res.json()
}

export interface StreamCallbacks {
  onCitations: (citations: Citation[]) => void
  onToken: (token: string) => void
  onDone: () => void
  onError: (error: string) => void
}

export interface StreamChatResult {
  abort: () => void
}

export async function streamChat(
  question: string,
  options: ChatOptions = {},
  callbacks: StreamCallbacks
): Promise<StreamChatResult> {
  const { nSources = 8, sourceTypes, authors, history } = options

  const abortController = new AbortController()

  // Start streaming in background
  ;(async () => {
    try {
      const res = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          n_sources: nSources,
          source_types: sourceTypes?.length ? sourceTypes : undefined,
          authors: authors?.length ? authors : undefined,
          history: history?.length ? history : undefined,
        }),
        signal: abortController.signal,
      })

      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(error.detail || `Request failed: ${res.statusText}`)
      }

      const reader = res.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete SSE lines
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'citations') {
                  callbacks.onCitations(data.data)
                } else if (data.type === 'token') {
                  callbacks.onToken(data.data)
                } else if (data.type === 'done') {
                  callbacks.onDone()
                }
              } catch {
                // Ignore malformed JSON
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
    } catch (err) {
      // Don't report error if it was due to intentional abort
      if (err instanceof Error && err.name === 'AbortError') {
        return
      }
      callbacks.onError(err instanceof Error ? err.message : 'Streaming failed')
    }
  })()

  return {
    abort: () => abortController.abort(),
  }
}
