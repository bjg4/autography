'use client'

import { useEffect, useRef, useState } from 'react'
import CitationCard from '@/components/CitationCard'
import AnswerDisplay from '@/components/AnswerDisplay'
import { streamChat, getSources, ChatResponse, Citation, SourcesResponse, ConversationTurn } from '@/lib/api'

const SOURCE_TYPE_LABELS: Record<string, { label: string; icon: string }> = {
  book_chapter: { label: 'Books', icon: '📖' },
  podcast_transcript: { label: 'Podcasts', icon: '🎙️' },
  essay: { label: 'Essays', icon: '📝' },
}

interface ThreadItem {
  question: string
  response: ChatResponse
}

export default function Home() {
  const [question, setQuestion] = useState('')
  const [thread, setThread] = useState<ThreadItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sources, setSources] = useState<SourcesResponse | null>(null)
  const threadEndRef = useRef<HTMLDivElement>(null)

  // Streaming state
  const [streamingAnswer, setStreamingAnswer] = useState('')
  const [streamingCitations, setStreamingCitations] = useState<Citation[]>([])
  const [currentQuestion, setCurrentQuestion] = useState('')

  // Filters
  const [selectedSourceTypes, setSelectedSourceTypes] = useState<string[]>([])
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([])
  const [showAuthorDropdown, setShowAuthorDropdown] = useState(false)

  useEffect(() => {
    getSources()
      .then(setSources)
      .catch((err) => console.error('Failed to load sources:', err))
  }, [])

  // Scroll to bottom when new content is added
  useEffect(() => {
    if (thread.length > 0) {
      threadEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [thread])

  // Build history from thread for context
  const getHistory = (): ConversationTurn[] => {
    return thread.map(item => ({
      question: item.question,
      answer: item.response.answer
    }))
  }

  const handleSubmit = async (q: string) => {
    if (!q.trim()) return

    setIsLoading(true)
    setError(null)
    setStreamingAnswer('')
    setStreamingCitations([])
    setCurrentQuestion(q.trim())
    setQuestion('')

    let finalAnswer = ''
    let finalCitations: Citation[] = []

    await streamChat(
      q.trim(),
      {
        sourceTypes: selectedSourceTypes.length > 0 ? selectedSourceTypes : undefined,
        authors: selectedAuthors.length > 0 ? selectedAuthors : undefined,
        history: getHistory(),
      },
      {
        onCitations: (citations) => {
          finalCitations = citations
          setStreamingCitations(citations)
        },
        onToken: (token) => {
          finalAnswer += token
          setStreamingAnswer(prev => prev + token)
        },
        onDone: () => {
          // Add to thread when done
          setThread(prev => [...prev, {
            question: q.trim(),
            response: {
              answer: finalAnswer,
              citations: finalCitations,
              follow_ups: [] // Follow-ups are embedded in answer after ---
            }
          }])
          setStreamingAnswer('')
          setStreamingCitations([])
          setCurrentQuestion('')
          setIsLoading(false)
        },
        onError: (errorMsg) => {
          setError(errorMsg)
          setStreamingAnswer('')
          setStreamingCitations([])
          setCurrentQuestion('')
          setIsLoading(false)
        }
      }
    )
  }

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleSubmit(question)
  }

  const handleFollowUp = (followUp: string) => {
    handleSubmit(followUp)
  }

  const startNewThread = () => {
    setThread([])
    setQuestion('')
    setError(null)
  }

  const scrollToCitation = (index: number, threadIndex: number) => {
    const element = document.getElementById(`citation-${threadIndex}-${index}`)
    element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  const toggleSourceType = (type: string) => {
    setSelectedSourceTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }

  const toggleAuthor = (author: string) => {
    setSelectedAuthors(prev =>
      prev.includes(author) ? prev.filter(a => a !== author) : [...prev, author]
    )
  }

  const clearFilters = () => {
    setSelectedSourceTypes([])
    setSelectedAuthors([])
  }

  const hasFilters = selectedSourceTypes.length > 0 || selectedAuthors.length > 0

  return (
    <main className="min-h-screen bg-[#FDFBF7]">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-[#2D2A26] tracking-tight">
            Autography
          </h1>
          <p className="text-[#7D756A] mt-2">
            Product management wisdom from the people who shaped it
          </p>
          {sources && (
            <p className="text-xs text-[#A89F91] mt-2">
              {sources.stats.total_documents} passages · {sources.authors.length} voices
            </p>
          )}
        </header>

        {/* Filters - only show when no thread or at start */}
        {thread.length === 0 && (
          <div className="mb-6">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="text-xs text-[#7D756A] mr-1">Filter by:</span>
              {Object.entries(SOURCE_TYPE_LABELS).map(([type, { label, icon }]) => (
                <button
                  key={type}
                  onClick={() => toggleSourceType(type)}
                  className={`px-3 py-1.5 text-xs rounded-full border transition-all ${
                    selectedSourceTypes.includes(type)
                      ? 'bg-[#C45A3B] text-white border-[#C45A3B]'
                      : 'bg-white text-[#5D574E] border-[#E5E0D8] hover:border-[#C45A3B]/50'
                  }`}
                >
                  {icon} {label}
                </button>
              ))}

              {/* Author Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowAuthorDropdown(!showAuthorDropdown)}
                  className={`px-3 py-1.5 text-xs rounded-full border transition-all flex items-center gap-1 ${
                    selectedAuthors.length > 0
                      ? 'bg-[#C45A3B] text-white border-[#C45A3B]'
                      : 'bg-white text-[#5D574E] border-[#E5E0D8] hover:border-[#C45A3B]/50'
                  }`}
                >
                  👤 {selectedAuthors.length > 0 ? `${selectedAuthors.length} authors` : 'Authors'}
                  <svg className={`w-3 h-3 transition-transform ${showAuthorDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showAuthorDropdown && sources && (
                  <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-[#E5E0D8] rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
                    {sources.authors.map(author => (
                      <button
                        key={author}
                        onClick={() => toggleAuthor(author)}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-[#F5F2ED] flex items-center justify-between ${
                          selectedAuthors.includes(author) ? 'text-[#C45A3B] font-medium' : 'text-[#5D574E]'
                        }`}
                      >
                        {author}
                        {selectedAuthors.includes(author) && (
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {hasFilters && (
                <button
                  onClick={clearFilters}
                  className="px-2 py-1 text-xs text-[#7D756A] hover:text-[#C45A3B] transition-colors"
                >
                  Clear all
                </button>
              )}
            </div>
          </div>
        )}

        {/* Initial Search - only show when no thread */}
        {thread.length === 0 && (
          <>
            <form onSubmit={handleFormSubmit} className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask anything about product management..."
                  className="w-full px-4 py-3.5 text-[15px] bg-white border border-[#E5E0D8] rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#C45A3B]/30 focus:border-[#C45A3B] placeholder:text-[#A89F91] transition-shadow"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !question.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-[#C45A3B] text-white text-sm font-medium rounded-lg hover:bg-[#a84832] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    'Ask'
                  )}
                </button>
              </div>
            </form>

            {/* Empty State Suggestions */}
            {!isLoading && !error && (
              <div className="text-center py-12">
                <p className="text-[#7D756A] mb-6">Try asking about:</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {[
                    'What makes a great product team?',
                    'How do I avoid building features nobody wants?',
                    'What is continuous discovery?',
                    'How should I think about product strategy?',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleSubmit(suggestion)}
                      className="px-4 py-2.5 bg-white border border-[#E5E0D8] rounded-lg text-sm text-[#5D574E] hover:border-[#C45A3B] hover:text-[#C45A3B] transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Conversation Thread */}
        {thread.length > 0 && (
          <div className="space-y-8">
            {/* New Thread Button */}
            <div className="flex justify-end">
              <button
                onClick={startNewThread}
                className="px-3 py-1.5 text-xs text-[#7D756A] hover:text-[#C45A3B] border border-[#E5E0D8] rounded-lg hover:border-[#C45A3B]/50 transition-colors"
              >
                + New thread
              </button>
            </div>

            {thread.map((item, threadIndex) => (
              <div key={threadIndex} className="space-y-4">
                {/* Question */}
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#C45A3B]/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm">👤</span>
                  </div>
                  <p className="text-[#2D2A26] font-medium pt-1">{item.question}</p>
                </div>

                {/* Answer */}
                <div className="ml-11">
                  <div className="p-5 bg-white rounded-xl border border-[#E5E0D8]">
                    <AnswerDisplay
                      answer={item.response.answer}
                      citations={item.response.citations}
                      onCitationClick={(index) => scrollToCitation(index, threadIndex)}
                    />
                  </div>

                  {/* Sources */}
                  {item.response.citations.length > 0 && (
                    <div className="mt-4">
                      <details className="group">
                        <summary className="text-xs font-medium text-[#7D756A] cursor-pointer hover:text-[#C45A3B] flex items-center gap-1">
                          <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                          {item.response.citations.length} sources
                        </summary>
                        <div className="mt-3 space-y-2">
                          {item.response.citations.map((citation) => (
                            <div key={citation.index} id={`citation-${threadIndex}-${citation.index}`}>
                              <CitationCard citation={citation} />
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}
                </div>

                {/* Divider between thread items */}
                {threadIndex < thread.length - 1 && (
                  <div className="border-t border-[#E5E0D8] my-6" />
                )}
              </div>
            ))}

            {/* Streaming response */}
            {isLoading && currentQuestion && (
              <div className="space-y-4">
                {/* Question */}
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#C45A3B]/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm">👤</span>
                  </div>
                  <p className="text-[#2D2A26] font-medium pt-1">{currentQuestion}</p>
                </div>

                {/* Streaming Answer */}
                <div className="ml-11">
                  <div className="p-5 bg-white rounded-xl border border-[#E5E0D8]">
                    {streamingAnswer ? (
                      <AnswerDisplay
                        answer={streamingAnswer}
                        citations={streamingCitations}
                        onCitationClick={() => {}}
                      />
                    ) : (
                      <div className="flex items-center gap-2 text-[#7D756A]">
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span className="text-sm">Searching knowledge base...</span>
                      </div>
                    )}
                    {streamingAnswer && (
                      <span className="inline-block w-2 h-4 bg-[#C45A3B] animate-pulse ml-0.5" />
                    )}
                  </div>

                  {/* Streaming Sources */}
                  {streamingCitations.length > 0 && (
                    <div className="mt-4">
                      <details className="group" open>
                        <summary className="text-xs font-medium text-[#7D756A] cursor-pointer hover:text-[#C45A3B] flex items-center gap-1">
                          <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                          {streamingCitations.length} sources found
                        </summary>
                        <div className="mt-3 space-y-2">
                          {streamingCitations.map((citation) => (
                            <div key={citation.index}>
                              <CitationCard citation={citation} />
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Follow-up questions for last response */}
            {!isLoading && thread.length > 0 && thread[thread.length - 1].response.follow_ups.length > 0 && (
              <div className="ml-11">
                <h3 className="text-xs font-medium text-[#7D756A] mb-3 uppercase tracking-wider">
                  Continue exploring
                </h3>
                <div className="flex flex-wrap gap-2">
                  {thread[thread.length - 1].response.follow_ups.map((followUp, i) => (
                    <button
                      key={i}
                      onClick={() => handleFollowUp(followUp)}
                      className="px-3 py-2 bg-[#F5F2ED] text-[#5D574E] rounded-lg text-sm hover:bg-[#EBE6DE] transition-colors text-left"
                    >
                      {followUp}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Follow-up input */}
            {!isLoading && (
              <div className="ml-11 pt-4">
                <form onSubmit={handleFormSubmit}>
                  <div className="relative">
                    <input
                      type="text"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Ask a follow-up question..."
                      className="w-full px-4 py-3 text-[15px] bg-white border border-[#E5E0D8] rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#C45A3B]/30 focus:border-[#C45A3B] placeholder:text-[#A89F91] transition-shadow"
                    />
                    <button
                      type="submit"
                      disabled={!question.trim()}
                      className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-[#C45A3B] text-white text-sm font-medium rounded-lg hover:bg-[#a84832] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      Ask
                    </button>
                  </div>
                </form>
              </div>
            )}

            <div ref={threadEndRef} />
          </div>
        )}
      </div>

      {/* Click outside to close dropdown */}
      {showAuthorDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowAuthorDropdown(false)}
        />
      )}
    </main>
  )
}
