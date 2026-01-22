'use client'

import { useEffect, useRef, useState } from 'react'
import CitationCard from '@/components/CitationCard'
import AnswerDisplay from '@/components/AnswerDisplay'
import { streamChat, getSources, ChatResponse, Citation, SourcesResponse, ConversationTurn } from '@/lib/api'

interface ThreadItem {
  question: string
  response: ChatResponse
}

interface Clip {
  id: string
  text: string
  source?: string
  timestamp: Date
}

const sourceTypeConfig: Record<string, { label: string; color: string }> = {
  essay: { label: 'Essay', color: 'bg-blue-50 text-blue-600' },
  book_chapter: { label: 'Book', color: 'bg-amber-50 text-amber-600' },
  podcast_transcript: { label: 'Podcast', color: 'bg-purple-50 text-purple-600' },
}

function SourceCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false)
  const typeConfig = sourceTypeConfig[citation.source_type] || { label: 'Source', color: 'bg-gray-50 text-gray-600' }

  // Get a preview of the content (first ~100 chars)
  const contentPreview = citation.content.slice(0, 120).trim() + (citation.content.length > 120 ? '...' : '')

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-[#E5E0D8]/60 overflow-hidden transition-all ${
        expanded ? 'shadow-md' : 'hover:shadow-md cursor-pointer'
      }`}
      onClick={() => !expanded && setExpanded(true)}
    >
      <div className="p-3">
        {/* Header row */}
        <div className="flex items-start gap-2.5">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#C45A3B]/10 text-[#C45A3B] flex items-center justify-center text-[10px] font-semibold">
            {citation.index}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs font-medium text-[#3D3833] leading-snug">
                {citation.title || 'Untitled'}
              </p>
              <span className={`flex-shrink-0 px-1.5 py-0.5 rounded text-[9px] font-medium ${typeConfig.color}`}>
                {typeConfig.label}
              </span>
            </div>
            <p className="text-[10px] text-[#9A8C7B] mt-0.5">
              {citation.author}
            </p>
          </div>
        </div>

        {/* Content preview */}
        <div className="mt-2 ml-7">
          <p className={`text-[11px] text-[#5D574E] leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}>
            {expanded ? citation.content : contentPreview}
          </p>
        </div>
      </div>

      {/* Expanded footer */}
      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-[#E5E0D8]/60 mt-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              setExpanded(false)
            }}
            className="text-[10px] text-[#9A8C7B] hover:text-[#C45A3B] transition-colors"
          >
            Show less
          </button>
        </div>
      )}
    </div>
  )
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

  // All citations from the conversation (for sidebar)
  const [allCitations, setAllCitations] = useState<Citation[]>([])

  // Clips state
  const [clips, setClips] = useState<Clip[]>([])
  const [clipsLoaded, setClipsLoaded] = useState(false)
  const [clipMode, setClipMode] = useState(false)
  const [showClipButton, setShowClipButton] = useState(false)
  const [clipButtonPos, setClipButtonPos] = useState({ x: 0, y: 0 })
  const [selectedText, setSelectedText] = useState('')
  const [justClipped, setJustClipped] = useState<string | null>(null)

  // Track seen citations for O(1) deduplication
  const seenCitationsRef = useRef<Set<string>>(new Set())

  // Load clips from localStorage
  useEffect(() => {
    const savedClips = localStorage.getItem('autography-clips')
    if (savedClips) {
      try {
        setClips(JSON.parse(savedClips))
      } catch {
        // Invalid JSON, start fresh
      }
    }
    setClipsLoaded(true)
  }, [])

  // Save clips to localStorage (only after initial load to avoid race condition)
  useEffect(() => {
    if (clipsLoaded) {
      localStorage.setItem('autography-clips', JSON.stringify(clips))
    }
  }, [clips, clipsLoaded])

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

  // Handle text selection for clipping (only in clip mode)
  useEffect(() => {
    if (!clipMode) {
      setShowClipButton(false)
      return
    }

    const handleSelection = () => {
      const selection = window.getSelection()
      const text = selection?.toString().trim()

      if (text && text.length > 10) {
        const range = selection?.getRangeAt(0)
        const rect = range?.getBoundingClientRect()
        if (rect) {
          setSelectedText(text)
          setClipButtonPos({ x: rect.left + rect.width / 2, y: rect.top - 10 })
          setShowClipButton(true)
        }
      } else {
        setShowClipButton(false)
      }
    }

    document.addEventListener('mouseup', handleSelection)
    return () => document.removeEventListener('mouseup', handleSelection)
  }, [clipMode])

  const handleClip = () => {
    if (selectedText) {
      const newClip: Clip = {
        id: Date.now().toString(),
        text: selectedText,
        timestamp: new Date(),
      }
      setClips(prev => [newClip, ...prev])
      setShowClipButton(false)
      setJustClipped(selectedText)
      window.getSelection()?.removeAllRanges()

      // Show confirmation briefly
      setTimeout(() => setJustClipped(null), 2000)
    }
  }

  const removeClip = (id: string) => {
    setClips(prev => prev.filter(c => c.id !== id))
  }

  // Build history from thread for context
  const getHistory = (): ConversationTurn[] => {
    return thread.map(item => ({
      question: item.question,
      answer: item.response.answer
    }))
  }

  // Extract follow-up questions from answer text
  const extractFollowUps = (answer: string): { cleanAnswer: string; followUps: string[] } => {
    let cleanAnswer = answer
    let followUpText = ''

    // Try different separator patterns
    if (answer.includes('\n---')) {
      const parts = answer.split('\n---')
      cleanAnswer = parts[0].trim()
      followUpText = parts[1] || ''
    } else if (answer.includes('---')) {
      const parts = answer.split('---')
      cleanAnswer = parts[0].trim()
      followUpText = parts[1] || ''
    } else if (answer.toLowerCase().includes('follow-up')) {
      const match = answer.match(/follow[- ]?up[s]?[:\s]*questions?[:\s]*/i)
      if (match) {
        const idx = answer.indexOf(match[0])
        cleanAnswer = answer.slice(0, idx).trim()
        followUpText = answer.slice(idx + match[0].length)
      }
    } else {
      return { cleanAnswer: answer, followUps: [] }
    }

    // Split by question marks to get individual questions
    const questions = followUpText
      .split('?')
      .map(q => q.replace(/^[-•\d.)\s\n]+/, '').trim())
      .filter(q => q.length > 15)
      .map(q => q + '?')
      .slice(0, 3)

    return { cleanAnswer, followUps: questions }
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
        history: getHistory(),
      },
      {
        onCitations: (citations) => {
          finalCitations = citations
          setStreamingCitations(citations)
          // Add to all citations for sidebar with O(1) deduplication
          setAllCitations(prev => {
            const newCitations: Citation[] = []
            for (const c of citations) {
              const key = `${c.title}|${c.author}`
              if (!seenCitationsRef.current.has(key)) {
                seenCitationsRef.current.add(key)
                newCitations.push(c)
              }
            }
            if (newCitations.length === 0) return prev
            // Cap at 100 citations to prevent unbounded growth
            const combined = [...prev, ...newCitations]
            return combined.slice(-100)
          })
        },
        onToken: (token) => {
          finalAnswer += token
          setStreamingAnswer(prev => prev + token)
        },
        onDone: () => {
          const { cleanAnswer, followUps } = extractFollowUps(finalAnswer)

          setThread(prev => [...prev, {
            question: q.trim(),
            response: {
              answer: cleanAnswer,
              citations: finalCitations,
              follow_ups: followUps
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

  const startNewThread = () => {
    setThread([])
    setAllCitations([])
    seenCitationsRef.current.clear()
    setQuestion('')
    setError(null)
  }

  const hasContent = thread.length > 0 || isLoading

  return (
    <main className={`min-h-screen bg-[#FDFBF7] ${clipMode ? 'cursor-crosshair' : ''}`}>
      {/* Clip Mode Banner */}
      {clipMode && (
        <div className="fixed top-0 left-0 right-0 z-40 bg-[#C45A3B] text-white py-2 px-4 flex items-center justify-center gap-3 text-sm">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0 0L12 12" />
          </svg>
          <span>Clip Mode: Select text to save it</span>
          <button
            onClick={() => setClipMode(false)}
            className="ml-4 px-3 py-1 bg-white/20 rounded hover:bg-white/30 transition-colors"
          >
            Done
          </button>
        </div>
      )}

      {/* Clip Button (floating, only in clip mode) */}
      {showClipButton && clipMode && (
        <button
          onClick={handleClip}
          style={{ left: clipButtonPos.x, top: clipButtonPos.y }}
          className="fixed z-50 -translate-x-1/2 -translate-y-full px-3 py-1.5 bg-[#C45A3B] text-white rounded-lg shadow-lg flex items-center gap-1.5 text-xs font-medium hover:bg-[#a84832] transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0 0L12 12" />
          </svg>
          Clip this
        </button>
      )}

      {/* Clipped confirmation toast */}
      {justClipped && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-[#2D2A26] text-white rounded-lg shadow-lg flex items-center gap-2 text-sm animate-pulse">
          <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Clipped!
        </div>
      )}

      <div className={`mx-auto px-4 py-8 ${hasContent ? 'max-w-5xl' : 'max-w-3xl'} ${clipMode ? 'pt-16' : ''}`}>
        {/* Header */}
        <header className={`mb-8 ${hasContent ? '' : 'text-center'}`}>
          <h1 className="text-3xl font-semibold text-[#2D2A26] tracking-tight">
            Autography
          </h1>
          <p className="text-[#7D756A] mt-2">
            Product management wisdom from the people who shaped it
          </p>
          {sources && !hasContent && (
            <p className="text-xs text-[#A89F91] mt-2">
              {sources.stats.total_documents} passages · {sources.authors.length} voices
            </p>
          )}
        </header>

        {/* Initial Search */}
        {!hasContent && (
          <>
            <form onSubmit={handleFormSubmit} className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask anything about product management..."
                  className="w-full px-4 py-3.5 text-[15px] bg-white border border-[#E5E0D8] rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#C45A3B]/30 focus:border-[#C45A3B] placeholder:text-[#A89F91]"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !question.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-[#C45A3B] text-white text-sm font-medium rounded-lg hover:bg-[#a84832] disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Ask
                </button>
              </div>
            </form>

            <div className="text-center py-12">
              <p className="text-[#7D756A] mb-6">Try asking about:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  'What makes a great product team?',
                  'How do I avoid building features nobody wants?',
                  'What is continuous discovery?',
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
          </>
        )}

        {/* Content layout when there's content */}
        {hasContent && (
          <div className="flex gap-8 justify-center">
            {/* Main Chat - centered */}
            <div className="w-full max-w-2xl">
              {/* Action buttons */}
              <div className="mb-6 flex items-center gap-2">
                <button
                  onClick={startNewThread}
                  className="px-3 py-1.5 text-xs text-[#7D756A] hover:text-[#C45A3B] border border-[#E5E0D8] rounded-lg hover:border-[#C45A3B]/50"
                >
                  + New thread
                </button>
                <button
                  onClick={() => setClipMode(true)}
                  className="px-3 py-1.5 text-xs text-[#7D756A] hover:text-[#C45A3B] border border-[#E5E0D8] rounded-lg hover:border-[#C45A3B]/50 flex items-center gap-1.5"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0 0L12 12" />
                  </svg>
                  Clip
                </button>
              </div>

              {/* Error */}
              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              {/* Thread */}
              <div className="space-y-6">
                {thread.map((item, idx) => (
                  <div key={idx} className="space-y-4">
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
                          onCitationClick={() => {}}
                        />
                      </div>

                      {/* Follow-up questions */}
                      {item.response.follow_ups.length > 0 && idx === thread.length - 1 && !isLoading && (
                        <div className="mt-4">
                          <p className="text-xs font-medium text-[#7D756A] mb-2 uppercase tracking-wider">
                            Continue exploring
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {item.response.follow_ups.map((followUp, i) => (
                              <button
                                key={i}
                                onClick={() => handleSubmit(followUp)}
                                className="px-3 py-2 bg-[#F5F2ED] text-[#5D574E] rounded-lg text-sm hover:bg-[#EBE6DE] text-left"
                              >
                                {followUp}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {idx < thread.length - 1 && <div className="border-t border-[#E5E0D8]" />}
                  </div>
                ))}

                {/* Streaming response */}
                {isLoading && currentQuestion && (
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-[#C45A3B]/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm">👤</span>
                      </div>
                      <p className="text-[#2D2A26] font-medium pt-1">{currentQuestion}</p>
                    </div>

                    <div className="ml-11">
                      <div className="p-5 bg-white rounded-xl border border-[#E5E0D8]">
                        {streamingAnswer ? (
                          <>
                            <AnswerDisplay
                              answer={streamingAnswer}
                              citations={streamingCitations}
                              onCitationClick={() => {}}
                            />
                            <span className="inline-block w-2 h-4 bg-[#C45A3B] animate-pulse ml-0.5" />
                          </>
                        ) : (
                          <div className="flex items-center gap-2 text-[#7D756A]">
                            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            <span className="text-sm">Searching knowledge base...</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Follow-up input */}
                {!isLoading && thread.length > 0 && (
                  <div className="ml-11 pt-2">
                    <form onSubmit={handleFormSubmit}>
                      <div className="relative">
                        <input
                          type="text"
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
                          placeholder="Ask a follow-up question..."
                          className="w-full px-4 py-3 text-[15px] bg-white border border-[#E5E0D8] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C45A3B]/30 focus:border-[#C45A3B] placeholder:text-[#A89F91]"
                        />
                        <button
                          type="submit"
                          disabled={!question.trim()}
                          className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-[#C45A3B] text-white text-sm font-medium rounded-lg hover:bg-[#a84832] disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          Ask
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                <div ref={threadEndRef} />
              </div>
            </div>

            {/* Floating Source Cards - sticky as you scroll */}
            {(allCitations.length > 0 || clips.length > 0) && (
              <div className="hidden lg:block w-64 flex-shrink-0">
                <div className="sticky top-8 pt-12 max-h-[calc(100vh-4rem)] overflow-y-auto">
                {/* Clips section */}
                {clips.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-[10px] font-semibold text-[#9A8C7B] uppercase tracking-wider mb-3">
                      Clips
                    </h4>
                    <div className="space-y-2.5">
                      {clips.map((clip) => (
                        <div
                          key={clip.id}
                          className="bg-white rounded-xl p-3 shadow-sm border border-[#E5E0D8]/60 group relative"
                        >
                          <div className="flex items-start gap-2">
                            <svg className="w-3.5 h-3.5 text-[#C45A3B] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0 0L12 12" />
                            </svg>
                            <p className="text-xs text-[#5D574E] line-clamp-3 leading-relaxed">{clip.text}</p>
                          </div>
                          <button
                            onClick={() => removeClip(clip.id)}
                            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-[#9A8C7B] hover:text-red-500 transition-opacity"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Sources section */}
                {(isLoading ? streamingCitations.length > 0 : allCitations.length > 0) && (
                  <div>
                    <h4 className="text-[10px] font-semibold text-[#9A8C7B] uppercase tracking-wider mb-3">
                      Sources
                    </h4>
                    <div className="space-y-2.5">
                      {(isLoading ? streamingCitations : allCitations).map((citation, idx) => (
                        <SourceCard key={`${citation.title}-${idx}`} citation={citation} />
                      ))}
                    </div>
                  </div>
                )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
