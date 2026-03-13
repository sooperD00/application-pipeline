/**
 * MetaAnalysis — display panel for Claude's cross-JD strategic observations.
 *
 * Updates live after each batch_complete during SSE streaming.
 * Collapsible because the text can be multi-paragraph (skill gap patterns,
 * apply-now vs scrape-more advice, LinkedIn exclusion filters).
 *
 * Renders nothing when text is null/empty — safe to include unconditionally.
 *  - `if (!text) return null` pattern
 */
import { useState } from 'react'

export default function MetaAnalysis({ text }) {
  const [expanded, setExpanded] = useState(true)

  if (!text) return null

  return (
    <div className="mt-6 rounded-lg bg-pipeline-800 border border-pipeline-700 overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-pipeline-300 hover:text-pipeline-100 transition-colors"
        data-testid="meta-analysis-toggle"
      >
        <span>Meta Analysis</span>
        <span className="text-pipeline-500 text-xs">{expanded ? '▾' : '▸'}</span>
      </button>
      {expanded && (
        // whitespace-pre-wrap: preserves the newlines from claude and still wraps at the container edge
        // - "I have structured plain text and I want it to look structured" escape hatch.
        <div
          className="px-4 pb-4 text-sm text-pipeline-300 whitespace-pre-wrap leading-relaxed"
          data-testid="meta-analysis-content"
        >
          {text}
        </div>
      )}
    </div>
  )
}
