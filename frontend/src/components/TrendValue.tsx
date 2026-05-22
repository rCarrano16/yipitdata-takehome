import { formatPercent, trendTone } from '../lib/format'

interface TrendValueProps {
  /** The fractional change, or null when it cannot be computed. */
  value: number | null
}

/**
 * A signed percent change, rendered bold and color-toned: green for a rise,
 * red for a fall. The explicit + / - sign carries the direction as text, so
 * the meaning never rests on color alone. A null value renders a muted "n/a".
 *
 * Shared by the QoQ / YoY trend badges and the per-panel range change on the
 * detail chart, so every trend figure in the app looks the same. The font
 * size is inherited from the caller, so the same atom works inline on a small
 * card label and larger beside a chart panel title.
 */
export default function TrendValue({ value }: TrendValueProps) {
  return (
    <span className={`trend-value trend-value--${trendTone(value)}`}>
      {value === null ? 'n/a' : formatPercent(value)}
    </span>
  )
}
