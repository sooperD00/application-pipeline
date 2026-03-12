/**
 * JDCard — the atomic card for a single job description.
 *
 * Displays: number badge, company, role, status dot.
 * Status colors map to the CSS theme variables:
 *   apply → green, maybe → yellow, no → red, pending → gray.
 *
 * Sprint 10 will add CSS transitions on status changes (SSE-driven).
 * For now this is a static display component with no interactivity.
 */

const STATUS_STYLES = {
  apply:   { dot: 'bg-status-apply',   label: 'Apply',   bg: 'border-status-apply/30' },
  maybe:   { dot: 'bg-status-maybe',   label: 'Maybe',   bg: 'border-status-maybe/30' },
  no:      { dot: 'bg-status-no',      label: 'No',      bg: 'border-status-no/30' },
  pending: { dot: 'bg-status-pending', label: 'Pending', bg: 'border-pipeline-700' },
}

export default function JDCard({ jd }) {
  const style = STATUS_STYLES[jd.status] ?? STATUS_STYLES.pending

  // Show company and role if available; fall back to a generic label.
  // Before analysis runs, these may be empty strings from the user's paste
  // (the backend stores "" not null for company/role).
  const title = jd.company || 'Untitled'
  const subtitle = jd.role || 'Role not specified'

  /* Nested Div Structure
  Outer div  — the card itself (border, background, padding)
  ├── First inner div  — flexbox ROW: number badge ← → status dot
  │   ├── span (number badge, pushed left)
  │   └── span (status dot + label, pushed right)
  └── Second inner div — text STACK below: company on top, role below
      ├── p (company, bold)
      └── p (role, dimmer)
  */
  return (
    /* border, background, padding */
    <div
      className={`p-3 rounded-lg bg-pipeline-800 border ${style.bg} transition-colors`}
      data-testid="jd-card"
      data-status={jd.status}
    >
      <div className="flex items-start justify-between gap-2">
        {/* Number badge */}
        <span className="shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-pipeline-700 text-pipeline-300 text-xs font-mono font-medium">
          {jd.number}
        </span>

        {/* Status dot + label */}
        <span className="flex items-center gap-1.5 text-xs text-pipeline-400">
          <span className={`w-2 h-2 rounded-full ${style.dot}`} />
          {style.label}
        </span>
      </div>

      <div className="mt-2">
        {/* Company (bold) */}
        <p className="text-sm font-medium text-pipeline-100 truncate" title={title}>
          {title}
        </p>
        {/* Role (dimmer) */}
        <p className="text-xs text-pipeline-400 truncate" title={subtitle}>
          {subtitle}
        </p>
      </div>
    </div>
  )
}
