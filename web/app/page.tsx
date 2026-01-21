'use client'

import { useEffect, useRef, useState } from 'react'
import CitationCard from '@/components/CitationCard'
import AnswerDisplay from '@/components/AnswerDisplay'
import { askQuestion, getSources, ChatResponse, SourcesResponse } from '@/lib/api'

const PROGRESS_STEPS = [
  { message: 'Understanding your question...', duration: 800 },
  { message: 'Searching across sources...', duration: 1500 },
  { message: 'Finding relevant passages...', duration: 1200 },
  { message: 'Ranking by relevance...', duration: 1000 },
  { message: 'Synthesizing answer with AI...', duration: 3000 },
]

export default function Home() {
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sources, setSources] = useState<SourcesResponse | null>(null)
  const [progressStep, setProgressStep] = useState(0)
  const citationsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getSources()
      .then(setSources)
      .catch((err) => console.error('Failed to load sources:', err))
  }, [])

  // Progress step timer
  useEffect(() => {
    if (!isLoading) {
      setProgressStep(0)
      return
    }

    let step = 0
    setProgressStep(0)

    const advanceStep = () => {
      if (step < PROGRESS_STEPS.length - 1) {
        step++
        setProgressStep(step)
        setTimeout(advanceStep, PROGRESS_STEPS[step].duration)
      }
    }

    const timer = setTimeout(advanceStep, PROGRESS_STEPS[0].duration)
    return () => clearTimeout(timer)
  }, [isLoading])

  const handleSubmit = async (q: string) => {
    if (!q.trim()) return

    setIsLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await askQuestion(q.trim())
      setResponse(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleSubmit(question)
  }

  const handleFollowUp = (followUp: string) => {
    setQuestion(followUp)
    handleSubmit(followUp)
  }

  const scrollToCitation = (index: number) => {
    const element = document.getElementById(`citation-${index}`)
    element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  return (
    <main className="min-h-screen bg-[#FDF8F3]">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-[#3D3833] mb-2">
            Autography
          </h1>
          <p className="text-lg text-[#9A8C7B]">
            The open evidence of product management
          </p>
          {sources && (
            <p className="text-sm text-[#9A8C7B] mt-1">
              {sources.stats.total_documents} sources from {sources.authors.length} authors
            </p>
          )}
        </header>

        {/* Search Input */}
        <form onSubmit={handleFormSubmit} className="mb-8">
          <div className="relative">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask anything about product management..."
              className="w-full px-5 py-4 text-lg bg-white border border-[#E8DDD4] rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#C45A3B] focus:border-transparent placeholder:text-[#9A8C7B]"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 bg-[#C45A3B] text-white rounded-xl hover:bg-[#a84832] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                'Ask'
              )}
            </button>
          </div>
        </form>

        {/* Error State */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
            {error}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="mb-8 p-6 bg-white rounded-2xl shadow-sm border border-[#E8DDD4]">
            <div className="space-y-4">
              {/* Progress steps */}
              <div className="space-y-2">
                {PROGRESS_STEPS.map((step, i) => (
                  <div
                    key={i}
                    className={`flex items-center gap-3 transition-opacity duration-300 ${
                      i < progressStep ? 'opacity-50' : i === progressStep ? 'opacity-100' : 'opacity-30'
                    }`}
                  >
                    {i < progressStep ? (
                      <svg className="w-5 h-5 text-[#C45A3B]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : i === progressStep ? (
                      <svg className="w-5 h-5 animate-spin text-[#C45A3B]" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-[#E8DDD4]" />
                    )}
                    <span className={`text-sm ${i === progressStep ? 'text-[#3D3833] font-medium' : 'text-[#9A8C7B]'}`}>
                      {step.message}
                    </span>
                  </div>
                ))}
              </div>

              {/* Progress bar */}
              <div className="h-1 bg-[#E8DDD4] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#C45A3B] transition-all duration-500 ease-out"
                  style={{ width: `${((progressStep + 1) / PROGRESS_STEPS.length) * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Response */}
        {response && !isLoading && (
          <div className="space-y-6">
            {/* Answer Card */}
            <div className="p-6 bg-white rounded-2xl shadow-sm border border-[#E8DDD4]">
              <AnswerDisplay
                answer={response.answer}
                citations={response.citations}
                onCitationClick={scrollToCitation}
              />
            </div>

            {/* Citations */}
            {response.citations.length > 0 && (
              <div ref={citationsRef}>
                <h3 className="text-sm font-medium text-[#9A8C7B] mb-3 uppercase tracking-wide">
                  Sources ({response.citations.length})
                </h3>
                <div className="space-y-2">
                  {response.citations.map((citation) => (
                    <div key={citation.index} id={`citation-${citation.index}`}>
                      <CitationCard citation={citation} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Follow-up Questions */}
            {response.follow_ups.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-[#9A8C7B] mb-3 uppercase tracking-wide">
                  Follow-up questions
                </h3>
                <div className="flex flex-wrap gap-2">
                  {response.follow_ups.map((followUp, i) => (
                    <button
                      key={i}
                      onClick={() => handleFollowUp(followUp)}
                      className="px-4 py-2 bg-[#E8DDD4] text-[#3D3833] rounded-full text-sm hover:bg-[#d4c9c0] transition-colors"
                    >
                      {followUp}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State with Suggestions */}
        {!response && !isLoading && !error && (
          <div className="text-center py-12">
            <p className="text-[#9A8C7B] mb-4">Try asking about:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                'How should a product team be structured?',
                'What makes a great one-pager?',
                'How do I avoid being a feature factory?',
                'What is continuous discovery?',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleFollowUp(suggestion)}
                  className="px-4 py-2 bg-white border border-[#E8DDD4] rounded-full text-sm text-[#3D3833] hover:border-[#C45A3B] hover:text-[#C45A3B] transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
