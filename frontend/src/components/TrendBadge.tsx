import { formatPercent, trendTone } from '../lib/format'
import TrendValue from './TrendValue'

interface TrendBadgeProps {
  /** Short display label, e.g. "QoQ" or "YoY". */
  label: string
  /** The spelled-out label for assistive tech, e.g. "Quarter over quarter". */
  description: string
  /** The fractional change, or null when it cannot be computed. */
  value: number | null
}

/**
 * One labelled trend signal as a pill: a short label and a signed percent
 * change, on a soft tint background toned to the direction. The label gives
 * the comparison (QoQ / YoY) in muted text; the percent is a bold, color-toned
 * TrendValue. Shared by the company-page summary cards and the series-page
 * AnalyticsRow, so the signal looks the same in both places.
 */
export default function TrendBadge({ label, description, value }: TrendBadgeProps) {
  const spoken = value === null ? 'not available' : formatPercent(value)
  return (
    <span
      className={`trend-badge trend-badge--${trendTone(value)}`}
      aria-label={`${description}: ${spoken}`}
    >
      {label} <TrendValue value={value} />
    </span>
  )
}
