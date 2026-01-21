'use client'

import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import ReactMarkdown from 'react-markdown'
import { Citation } from '@/lib/api'

interface AnswerDisplayProps {
  answer: string
  citations: Citation[]
  onCitationClick?: (index: number) => void
}

function CitationBadge({
  index,
  citation,
  onClick
}: {
  index: number
  citation?: Citation
  onClick?: () => void
}) {
  const [showPreview, setShowPreview] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleMouseEnter = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setPosition({
        top: rect.top - 8,
        left: rect.left + rect.width / 2
      })
    }
    setShowPreview(true)
  }

  return (
    <>
      <button
        ref={buttonRef}
        onClick={onClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShowPreview(false)}
        className="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 mx-0.5 text-xs font-semibold bg-[#C45A3B]/15 text-[#C45A3B] rounded-full hover:bg-[#C45A3B]/25 transition-colors align-middle"
        title={`View source ${index}`}
      >
        {index}
      </button>

      {/* Hover Preview - rendered via portal to avoid nesting issues */}
      {mounted && showPreview && citation && createPortal(
        <div
          className="fixed w-72 p-3 bg-white rounded-lg shadow-xl border border-[#E8DDD4] z-[9999] pointer-events-none"
          style={{
            top: position.top,
            left: position.left,
            transform: 'translate(-50%, -100%)'
          }}
        >
          <div className="text-xs font-semibold text-[#3D3833] mb-1 line-clamp-2">
            {citation.title}
          </div>
          <div className="text-xs text-[#9A8C7B] mb-2">
            {citation.author}
          </div>
          <div className="text-xs text-[#3D3833]/70 line-clamp-3 leading-relaxed">
            {citation.content.slice(0, 200)}...
          </div>
        </div>,
        document.body
      )}
    </>
  )
}

export default function AnswerDisplay({ answer, citations, onCitationClick }: AnswerDisplayProps) {
  const citationMap = new Map(citations.map(c => [c.index, c]))

  const processText = (text: string): React.ReactNode[] => {
    const parts = text.split(/(\[\d+\])/g)
    return parts.map((part, i) => {
      const match = part.match(/^\[(\d+)\]$/)
      if (match) {
        const citationIndex = parseInt(match[1], 10)
        const citation = citationMap.get(citationIndex)
        return (
          <CitationBadge
            key={i}
            index={citationIndex}
            citation={citation}
            onClick={() => onCitationClick?.(citationIndex)}
          />
        )
      }
      return <span key={i}>{part}</span>
    })
  }

  const processChildren = (children: React.ReactNode): React.ReactNode => {
    if (typeof children === 'string') {
      return processText(children)
    }
    if (Array.isArray(children)) {
      return children.map((child, i) =>
        typeof child === 'string' ? <span key={i}>{processText(child)}</span> : child
      )
    }
    return children
  }

  return (
    <div className="prose prose-stone prose-headings:text-[#3D3833] prose-headings:font-semibold prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-3 prose-h3:text-lg prose-p:my-3 prose-ul:my-3 prose-li:my-1 max-w-none">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p>{processChildren(children)}</p>,
          li: ({ children }) => <li>{processChildren(children)}</li>,
          strong: ({ children }) => <strong>{processChildren(children)}</strong>,
          em: ({ children }) => <em>{processChildren(children)}</em>,
        }}
      >
        {answer}
      </ReactMarkdown>
    </div>
  )
}
