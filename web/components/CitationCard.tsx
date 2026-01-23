'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Citation } from '@/lib/api'

interface CitationCardProps {
  citation: Citation
  compact?: boolean
}

export default function CitationCard({ citation, compact = false }: CitationCardProps) {
  const [expanded, setExpanded] = useState(false)

  const typeIcons: Record<string, string> = {
    essay: '📝',
    book_chapter: '📖',
    podcast_transcript: '🎙️',
  }

  const typeLabels: Record<string, string> = {
    essay: 'Essay',
    book_chapter: 'Book',
    podcast_transcript: 'Podcast',
  }

  // Compact mode for sidebar
  if (compact) {
    return (
      <div className="flex items-start gap-2 p-2 rounded-lg hover:bg-[#F5F2ED] transition-colors group">
        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#C45A3B]/10 text-[#C45A3B] flex items-center justify-center text-[10px] font-bold">
          {citation.index}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-[#3D3833] truncate">
            {citation.title || 'Untitled'}
          </p>
          <p className="text-[10px] text-[#9A8C7B] truncate">
            {typeIcons[citation.source_type] || '📄'} {citation.author}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-[#E8DDD4] bg-white overflow-hidden transition-shadow hover:shadow-md">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-[#FDF8F3]/50 transition-colors"
      >
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-[#C45A3B]/10 text-[#C45A3B] flex items-center justify-center text-xs font-bold">
          {citation.index}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm">{typeIcons[citation.source_type] || '📄'}</span>
            <span className="font-medium text-sm text-[#3D3833]">
              {citation.title || 'Untitled'}
            </span>
          </div>
          <p className="text-xs text-[#9A8C7B] mt-0.5">
            {citation.author}
            {citation.metadata.book_title ? ` · ${String(citation.metadata.book_title)}` : null}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[#9A8C7B] hidden sm:inline">
            {typeLabels[citation.source_type] || 'Source'}
          </span>
          <svg
            className={`w-5 h-5 text-[#9A8C7B] flex-shrink-0 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-[#E8DDD4]">
          <div className="mt-3 bg-[#FDF8F3] rounded-lg p-4 prose prose-sm prose-stone max-w-none prose-p:my-2 prose-headings:text-[#3D3833] prose-headings:mt-3 prose-headings:mb-2">
            <ReactMarkdown>
              {citation.content}
            </ReactMarkdown>
          </div>
          {citation.metadata.source_url ? (
            <a
              href={String(citation.metadata.source_url)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 mt-3 text-xs text-[#C45A3B] hover:underline"
            >
              View original source →
            </a>
          ) : null}
        </div>
      )}
    </div>
  )
}
