'use client'

import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { usePostHog } from 'posthog-js/react'
import CitationCard from '@/components/CitationCard'
import AnswerDisplay from '@/components/AnswerDisplay'
import { streamChat, getSources, getSuggestions, ChatResponse, Citation, SourcesResponse, ConversationTurn } from '@/lib/api'

interface ThreadItem {
  question: string
  response: ChatResponse
}

interface Clip {
  id: string
  text: string
  question?: string  // The question that generated this response
  source?: string
  author?: string
  sourceType?: string
  timestamp: Date
}

const sourceTypeConfig: Record<string, { label: string; color: string }> = {
  essay: { label: 'Essay', color: 'bg-blue-50 text-blue-600' },
  book_chapter: { label: 'Book', color: 'bg-amber-50 text-amber-600' },
  podcast_transcript: { label: 'Podcast', color: 'bg-purple-50 text-purple-600' },
}

const DEFAULT_SUGGESTIONS = [
  'What makes a great product team?',
  'How do I avoid building features nobody wants?',
  'What is continuous discovery?',
]

function SourcesList({ citations, keyPrefix }: { citations: Citation[]; keyPrefix: string }) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [showFade, setShowFade] = useState(true)

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return

    const checkScroll = () => {
      // Show fade only if not scrolled to bottom
      const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 20
      setShowFade(!isAtBottom && el.scrollHeight > el.clientHeight)
    }

    checkScroll()
    el.addEventListener('scroll', checkScroll)
    // Also check on resize
    const observer = new ResizeObserver(checkScroll)
    observer.observe(el)

    return () => {
      el.removeEventListener('scroll', checkScroll)
      observer.disconnect()
    }
  }, [citations])

  return (
    <div className="relative flex-1 min-h-0">
      <div
        ref={scrollRef}
        className="h-full overflow-y-auto space-y-2.5 pr-1"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        <style jsx>{`div::-webkit-scrollbar { display: none; }`}</style>
        {citations.map((citation, cidx) => (
          <SourceCard key={`${keyPrefix}-${cidx}`} citation={citation} />
        ))}
      </div>
      {/* Fade gradient - only show if more content below */}
      {showFade && (
        <div className="absolute bottom-0 left-0 right-1 h-12 bg-gradient-to-t from-[#FDFBF7] to-transparent pointer-events-none" />
      )}
    </div>
  )
}

function SourceCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false)
  const typeConfig = sourceTypeConfig[citation.source_type] || { label: 'Source', color: 'bg-gray-50 text-gray-600' }

  const contentPreview = citation.content.slice(0, 120).trim() + (citation.content.length > 120 ? '...' : '')

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-[#E5E0D8]/60 overflow-hidden transition-all ${
        expanded ? 'shadow-md' : 'hover:shadow-md cursor-pointer'
      }`}
      onClick={() => !expanded && setExpanded(true)}
    >
      <div className="p-3">
        <div className="flex items-start gap-2.5">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#C45A3B]/10 text-[#C45A3B] flex items-center justify-center text-[10px] font-semibold">
            {citation.index}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs font-medium text-[#3D3833] leading-snug">
                {citation.title || 'Untitled'}
              </p>
              <div className="flex items-center gap-1.5">
                <span className={`flex-shrink-0 px-1.5 py-0.5 rounded text-[9px] font-medium ${typeConfig.color}`}>
                  {typeConfig.label}
                </span>
                {expanded && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setExpanded(false)
                    }}
                    className="flex-shrink-0 w-5 h-5 rounded-full bg-[#F5F2ED] hover:bg-[#E5E0D8] flex items-center justify-center transition-colors"
                    title="Collapse"
                  >
                    <svg className="w-3 h-3 text-[#7D756A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
            <p className="text-[10px] text-[#9A8C7B] mt-0.5">
              {citation.author}
            </p>
          </div>
        </div>

        <div className="mt-2 ml-7">
          <p className={`text-[11px] text-[#5D574E] leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}>
            {expanded ? citation.content : contentPreview}
          </p>
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  const posthog = usePostHog()
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

  // Track which response is currently visible (for sidebar)
  const [visibleResponseIndex, setVisibleResponseIndex] = useState<number>(-1)
  const responseRefs = useRef<(HTMLDivElement | null)[]>([])

  // Suggestions state (null = loading, array = loaded)
  const [suggestions, setSuggestions] = useState<string[] | null>(null)

  // Clips state
  const [clips, setClips] = useState<Clip[]>([])
  const [clipsLoaded, setClipsLoaded] = useState(false)
  const [clipMode, setClipMode] = useState(false)
  const [showClipButton, setShowClipButton] = useState(false)
  const [clipButtonPos, setClipButtonPos] = useState({ x: 0, y: 0 })
  const [selectedText, setSelectedText] = useState('')
  const [justClipped, setJustClipped] = useState<string | null>(null)
  const [drawerExpanded, setDrawerExpanded] = useState(false)

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

  // Save clips to localStorage
  useEffect(() => {
    if (clipsLoaded) {
      localStorage.setItem('autography-clips', JSON.stringify(clips))
    }
  }, [clips, clipsLoaded])

  useEffect(() => {
    getSources()
      .then(setSources)
      .catch((err) => console.error('Failed to load sources:', err))

    getSuggestions()
      .then(setSuggestions)
      .catch((err) => {
        console.error('Failed to load suggestions:', err)
        setSuggestions(DEFAULT_SUGGESTIONS)
      })
  }, [])

  // IntersectionObserver to track which response is visible (single observer for all elements)
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
            const index = responseRefs.current.indexOf(entry.target as HTMLDivElement)
            if (index !== -1) setVisibleResponseIndex(index)
          }
        })
      },
      { threshold: [0.3, 0.5, 0.7], rootMargin: '-100px 0px -100px 0px' }
    )

    responseRefs.current.forEach((ref) => ref && observer.observe(ref))

    return () => observer.disconnect()
  }, [thread.length])

  // Scroll when user submits new question
  const shouldScrollRef = useRef(false)
  useEffect(() => {
    if (shouldScrollRef.current && currentQuestion) {
      threadEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      shouldScrollRef.current = false
    }
  }, [currentQuestion])

  // Handle text selection for clipping
  useEffect(() => {
    if (!clipMode) {
      setShowClipButton(false)
      return
    }

    const handleSelection = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (target.closest('[data-clip-button]')) {
        return
      }

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

  const handleClip = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const textToClip = selectedText
    if (textToClip) {
      // Find the current question context
      const currentQ = isLoading ? currentQuestion : (thread[visibleResponseIndex]?.question || thread[thread.length - 1]?.question)

      // Try to find which citation this text came from
      const currentCitations = isLoading ? streamingCitations : (thread[visibleResponseIndex]?.response.citations || [])
      const matchingCitation = currentCitations.find(c =>
        c.content.toLowerCase().includes(textToClip.toLowerCase().slice(0, 50))
      )

      const newClip: Clip = {
        id: Date.now().toString(),
        text: textToClip,
        question: currentQ,
        source: matchingCitation?.title,
        author: matchingCitation?.author,
        sourceType: matchingCitation?.source_type,
        timestamp: new Date(),
      }
      setClips(prev => [newClip, ...prev])
      setShowClipButton(false)

      // Track clip event (safe if PostHog not initialized)
      posthog?.capture?.('clip_saved', {
        text_length: textToClip.length,
        has_source: !!matchingCitation,
        source_type: matchingCitation?.source_type,
      })
      setSelectedText('')
      setJustClipped(textToClip)
      window.getSelection()?.removeAllRanges()

      setTimeout(() => setJustClipped(null), 2000)
    }
  }

  const removeClip = (id: string) => {
    setClips(prev => prev.filter(c => c.id !== id))
  }

  const copyClip = async (clip: Clip) => {
    await navigator.clipboard.writeText(clip.text)
  }

  const exportClips = () => {
    const text = clips.map(c => {
      let entry = `"${c.text}"`
      if (c.source) entry += `\n— ${c.source}`
      if (c.author) entry += `, ${c.author}`
      if (c.question) entry += `\n(From: "${c.question}")`
      return entry
    }).join('\n\n---\n\n')

    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'autography-clips.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  const clearAllClips = () => {
    if (confirm('Clear all clips?')) {
      setClips([])
    }
  }

  const getHistory = (): ConversationTurn[] => {
    return thread.slice(-3).map(item => ({
      question: item.question,
      answer: item.response.answer
    }))
  }

  const extractFollowUps = (answer: string): { cleanAnswer: string; followUps: string[] } => {
    // Look for --- separator
    const separatorIndex = answer.lastIndexOf('\n---')
    if (separatorIndex === -1) {
      return { cleanAnswer: answer, followUps: [] }
    }

    const cleanAnswer = answer.slice(0, separatorIndex).trim()
    const followUpText = answer.slice(separatorIndex + 4) // Skip "\n---"

    // Extract bullet points - each line starting with - is a question
    const questions = followUpText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.startsWith('-') || line.startsWith('•'))
      .map(line => line.replace(/^[-•]\s*/, '').trim())
      .filter(q => q.length > 10 && q.includes('?'))
      .slice(0, 3)

    return { cleanAnswer, followUps: questions }
  }

  const handleSubmit = async (q: string) => {
    if (!q.trim()) return

    // Track search event (safe if PostHog not initialized)
    posthog?.capture?.('search_submitted', {
      query: q.trim(),
      is_followup: thread.length > 0,
      thread_depth: thread.length,
    })

    shouldScrollRef.current = true
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
      { history: getHistory() },
      {
        onCitations: (citations) => {
          finalCitations = citations
          setStreamingCitations(citations)
        },
        onToken: (token) => {
          finalAnswer += token
          // Direct state update - plain text is cheap to render
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
          setCurrentQuestion('')
          setIsLoading(false)
          // Set visible to the new response
          setVisibleResponseIndex(thread.length)
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
    setStreamingCitations([])
    setQuestion('')
    setError(null)
    setVisibleResponseIndex(-1)
  }

  const hasContent = thread.length > 0 || isLoading

  // Get citations for the sidebar based on what's visible
  const getSidebarCitations = (): { citations: Citation[]; label: string } => {
    if (isLoading && streamingCitations.length > 0) {
      return { citations: streamingCitations, label: currentQuestion }
    }
    if (visibleResponseIndex >= 0 && thread[visibleResponseIndex]) {
      return {
        citations: thread[visibleResponseIndex].response.citations,
        label: thread[visibleResponseIndex].question
      }
    }
    if (thread.length > 0) {
      const lastIdx = thread.length - 1
      return {
        citations: thread[lastIdx].response.citations,
        label: thread[lastIdx].question
      }
    }
    return { citations: [], label: '' }
  }

  const { citations: sidebarCitations, label: sidebarLabel } = getSidebarCitations()

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

      {/* Clip Button */}
      {showClipButton && clipMode && (
        <button
          data-clip-button
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

      {/* Clipped toast */}
      {justClipped && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-[#2D2A26] text-white rounded-lg shadow-lg flex items-center gap-2 text-sm">
          <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Clipped!
        </div>
      )}

      <div className={`mx-auto px-4 py-8 ${clipMode ? 'pt-16' : ''}`}>
        {/* Initial state - centered, narrower */}
        {!hasContent && (
          <div className="max-w-3xl mx-auto">
            {/* Header */}
            <header className="mb-8 text-center">
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

            <form onSubmit={handleFormSubmit} className="mb-6">
              <div className="relative">
                <textarea
                  value={question}
                  onChange={(e) => {
                    setQuestion(e.target.value)
                    // Auto-resize textarea
                    e.target.style.height = 'auto'
                    e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px'
                  }}
                  onKeyDown={(e) => {
                    // Submit on Enter (without Shift)
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      if (question.trim() && !isLoading) {
                        handleFormSubmit(e as unknown as React.FormEvent)
                      }
                    }
                  }}
                  placeholder="Ask anything about product management..."
                  rows={1}
                  className="w-full px-3 py-3.5 pr-16 md:px-4 md:pr-24 text-base md:text-[15px] bg-white border border-[#E5E0D8] rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#C45A3B]/30 focus:border-[#C45A3B] placeholder:text-[#A89F91] resize-none"
                  disabled={isLoading}
                />
                <div className="absolute right-1.5 md:right-3 top-1/2 -translate-y-1/2">
                  <button
                    type="submit"
                    disabled={isLoading || !question.trim()}
                    className="px-2.5 py-1.5 md:px-4 md:py-2 bg-[#C45A3B] text-white text-sm font-medium rounded-lg hover:bg-[#a84832] disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    Ask
                  </button>
                </div>
              </div>
            </form>

            <div className="text-center py-12">
              <p className="text-[#7D756A] mb-6">Try asking about:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {suggestions === null ? (
                  // Loading skeleton
                  <>
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className="h-10 bg-[#F5F2ED] border border-[#E5E0D8] rounded-lg animate-pulse"
                        style={{ width: `${120 + i * 40}px` }}
                      />
                    ))}
                  </>
                ) : (
                  suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleSubmit(suggestion)}
                      className="px-4 py-2.5 bg-white border border-[#E5E0D8] rounded-lg text-sm text-[#5D574E] hover:border-[#C45A3B] hover:text-[#C45A3B] transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* Footer */}
            <footer className="mt-16 text-center">
              <p className="text-[10px] text-[#A89F91] uppercase tracking-widest">
                Made by GullyGorge in Portland, Ore
              </p>
            </footer>
          </div>
        )}

        {/* Content layout - response+sources as one centered unit */}
        {hasContent && (
          <div className="max-w-[920px] mx-auto">
            {/* Header (compact) */}
            <header className="mb-6">
              <h1 className="text-2xl font-semibold text-[#2D2A26] tracking-tight">
                Autography
              </h1>
              <p className="text-sm text-[#7D756A] mt-1">
                Product management wisdom from the people who shaped it
              </p>
            </header>

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
                {clips.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 bg-[#C45A3B]/10 text-[#C45A3B] rounded-full text-[10px] font-medium">
                    {clips.length}
                  </span>
                )}
              </button>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Thread - each response+sources as one unit */}
            <div className="space-y-10">
              {thread.map((item, idx) => (
                <div
                  key={idx}
                  ref={el => { responseRefs.current[idx] = el }}
                >
                  {/* Question + Sources row - aligned with response */}
                  <div className="flex gap-6 items-start">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-[#C45A3B]/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm">👤</span>
                      </div>
                      <p className="text-[#2D2A26] font-medium pt-1">{item.question}</p>
                    </div>
                    {/* Spacer for sources column alignment */}
                    <div className="hidden lg:block w-56 flex-shrink-0" />
                  </div>

                  {/* Answer + Sources row - aligned */}
                  <div className="flex gap-6 items-stretch ml-11 mt-3">
                    {/* Answer */}
                    <div className="flex-1 min-w-0">
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

                      {/* Sources - inline on smaller screens */}
                      <div className="lg:hidden mt-4">
                        <details className="group">
                          <summary className="text-xs text-[#9A8C7B] cursor-pointer hover:text-[#7D756A] list-none flex items-center gap-1">
                            <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                            {item.response.citations.length} sources
                          </summary>
                          <div className="mt-3 grid gap-2 sm:grid-cols-2">
                            {item.response.citations.map((citation, cidx) => (
                              <SourceCard key={`inline-${idx}-${cidx}`} citation={citation} />
                            ))}
                          </div>
                        </details>
                      </div>
                    </div>

                    {/* Sources - alongside on lg screens */}
                    <div className="hidden lg:flex lg:flex-col w-56 flex-shrink-0">
                      <h4 className="text-[10px] font-semibold text-[#9A8C7B] uppercase tracking-wider mb-2 -mt-6">
                        Sources
                      </h4>
                      <SourcesList citations={item.response.citations} keyPrefix={`${idx}`} />
                    </div>
                  </div>

                  {idx < thread.length - 1 && (
                    <div className="border-t border-[#E5E0D8] mt-8" />
                  )}
                </div>
              ))}

              {/* Streaming response */}
              {isLoading && currentQuestion && (
                <div>
                  {/* Question + Sources row - aligned with response */}
                  <div className="flex gap-6 items-start">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-[#C45A3B]/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm">👤</span>
                      </div>
                      <p className="text-[#2D2A26] font-medium pt-1">{currentQuestion}</p>
                    </div>
                    {/* Spacer for sources column alignment */}
                    <div className="hidden lg:block w-56 flex-shrink-0" />
                  </div>

                  {/* Answer + Sources row - aligned */}
                  <div className="flex gap-6 items-stretch ml-11 mt-3">
                    {/* Answer */}
                    <div className="flex-1 min-w-0">
                      <div className="p-5 bg-white rounded-xl border border-[#E5E0D8]">
                        {streamingAnswer ? (
                          <div className="prose prose-stone prose-headings:text-[#3D3833] prose-headings:font-semibold prose-p:my-3 max-w-none whitespace-pre-wrap text-[#3D3833]">
                            {streamingAnswer}
                            <span className="inline-block w-2 h-4 bg-[#C45A3B] animate-pulse ml-0.5 align-middle" />
                          </div>
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

                    {/* Streaming sources - alongside on lg screens */}
                    {streamingCitations.length > 0 && (
                      <div className="hidden lg:flex lg:flex-col w-56 flex-shrink-0">
                        <h4 className="text-[10px] font-semibold text-[#9A8C7B] uppercase tracking-wider mb-2 -mt-6">
                          Sources
                        </h4>
                        <SourcesList citations={streamingCitations} keyPrefix="streaming" />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Follow-up input */}
              {!isLoading && thread.length > 0 && (
                <div className="pl-0 md:pl-11 pt-2">
                  <form onSubmit={handleFormSubmit}>
                    <div className="relative lg:mr-[15.5rem]">
                      <textarea
                        value={question}
                        onChange={(e) => {
                          setQuestion(e.target.value)
                          // Auto-resize textarea
                          e.target.style.height = 'auto'
                          e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px'
                        }}
                        onKeyDown={(e) => {
                          // Submit on Enter (without Shift)
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault()
                            if (question.trim()) {
                              handleFormSubmit(e as unknown as React.FormEvent)
                            }
                          }
                        }}
                        placeholder="Ask a follow-up question..."
                        rows={1}
                        className="w-full px-3 py-3 pr-16 md:px-4 md:pr-24 text-base md:text-[15px] bg-white border border-[#E5E0D8] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C45A3B]/30 focus:border-[#C45A3B] placeholder:text-[#A89F91] resize-none"
                      />
                      <div className="absolute right-1.5 md:right-3 top-1/2 -translate-y-1/2">
                        <button
                          type="submit"
                          disabled={!question.trim()}
                          className="px-2.5 py-1.5 md:px-4 md:py-2 bg-[#C45A3B] text-white text-sm font-medium rounded-lg hover:bg-[#a84832] disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
                        >
                          Ask
                        </button>
                      </div>
                    </div>
                  </form>
                </div>
              )}

              <div ref={threadEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* Floating Clips Drawer */}
      {clips.length > 0 && (
        <div className={`fixed bottom-0 left-0 right-0 z-30 transition-transform duration-300 ${drawerExpanded ? 'translate-y-0' : 'translate-y-[calc(100%-2.75rem)]'}`}>
          {/* Drawer header */}
          <div
            className="bg-white border-t border-x border-[#E5E0D8] text-[#3D3833] px-4 py-2 flex items-center justify-between cursor-pointer rounded-t-xl mx-4 md:mx-auto md:max-w-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.08)]"
            onClick={() => setDrawerExpanded(!drawerExpanded)}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-[#C45A3B]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0 0L12 12" />
              </svg>
              <span className="text-sm font-medium">Your Clips</span>
              <span className="px-1.5 py-0.5 bg-[#C45A3B]/10 text-[#C45A3B] rounded text-xs font-medium">{clips.length}</span>
            </div>
            <div className="flex items-center gap-2">
              {drawerExpanded && (
                <>
                  <button
                    onClick={(e) => { e.stopPropagation(); exportClips() }}
                    className="px-2 py-1 text-[10px] text-[#7D756A] hover:text-[#C45A3B] border border-[#E5E0D8] rounded hover:border-[#C45A3B]/50"
                  >
                    Export
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); clearAllClips() }}
                    className="px-2 py-1 text-[10px] text-[#7D756A] hover:text-red-500 border border-[#E5E0D8] rounded hover:border-red-200"
                  >
                    Clear
                  </button>
                </>
              )}
              <svg
                className={`w-5 h-5 text-[#9A8C7B] transition-transform ${drawerExpanded ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            </div>
          </div>

          {/* Drawer content */}
          <div className="bg-white border-x border-[#E5E0D8] px-4 pb-4 mx-4 md:mx-auto md:max-w-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.08)] max-h-80 overflow-y-auto">
            <div className="space-y-3 pt-3">
              {clips.map((clip) => {
                const typeConfig = clip.sourceType ? sourceTypeConfig[clip.sourceType] : null
                return (
                  <div
                    key={clip.id}
                    className="bg-[#F9F7F4] rounded-xl p-4 group relative border border-[#E5E0D8]/60"
                  >
                    {/* Question context */}
                    {clip.question && (
                      <div className="mb-2 pb-2 border-b border-[#E5E0D8]/60">
                        <p className="text-[10px] text-[#9A8C7B]">
                          From: "{clip.question}"
                        </p>
                      </div>
                    )}

                    {/* Source info */}
                    {(clip.source || clip.author) && (
                      <div className="flex items-center gap-2 mb-2">
                        {typeConfig && (
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${typeConfig.color}`}>
                            {typeConfig.label}
                          </span>
                        )}
                        <span className="text-[10px] text-[#9A8C7B] truncate">
                          {clip.source && clip.author ? `${clip.source} · ${clip.author}` : clip.source || clip.author}
                        </span>
                      </div>
                    )}

                    <p className="text-sm text-[#3D3833] leading-relaxed pr-8">{clip.text}</p>

                    {/* Actions - always visible on mobile, hover on desktop */}
                    <div className="absolute top-3 right-3 flex items-center gap-1 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => { e.stopPropagation(); copyClip(clip) }}
                        className="w-6 h-6 rounded-full bg-white border border-[#E5E0D8] flex items-center justify-center text-[#9A8C7B] hover:text-[#C45A3B] hover:border-[#C45A3B]/50 transition-colors"
                        title="Copy"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); removeClip(clip.id) }}
                        className="w-6 h-6 rounded-full bg-white border border-[#E5E0D8] flex items-center justify-center text-[#9A8C7B] hover:text-red-500 hover:border-red-200 transition-colors"
                        title="Remove"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
