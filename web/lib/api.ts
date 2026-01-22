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
