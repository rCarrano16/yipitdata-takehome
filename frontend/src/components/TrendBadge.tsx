import { formatPercent } from '../lib/format'

interface TrendBadgeProps {
  /** Short display label, e.g. "QoQ" or "YoY". */
  label: string
  /** The spelled-out label for assistive tech, e.g. "Quarter over quarter". */
  description: string
  /** The fractional change, or null when it cannot be computed. */
  value: number | null
}

/**
 * A small pill showing one trend signal: a label and a signed percent change,
 * tinted green for a rise and red for a fall. The explicit + / - sign carries
 * the direction as text, so the meaning never depends on color alone (WCAG
 * 1.4.1). A null value (no comparable quarter) renders a neutral "n/a" pill.
 *
 * Shared by the company-page summary cards and the series-page AnalyticsRow, so
 * the same signal looks the same everywhere.
 */
export default function TrendBadge({ label, description, value }: TrendBadgeProps) {
  let tone = 'neutral'
  if (value !== null && value > 0) tone = 'positive'
  else if (value !== null && value < 0) tone = 'negative'

  const text = value === null ? 'n/a' : formatPercent(value)
  const ariaLabel =
    value === null ? `${description}: not available` : `${description}: ${text}`

  return (
    <span className={`trend-badge trend-badge--${tone}`} aria-label={ariaLabel}>
      {label} <span className="trend-badge-value">{text}</span>
    </span>
  )
}
