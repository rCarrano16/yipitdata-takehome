import type { SeriesAnalytics } from '../api/types'
import { formatPeriod } from '../lib/format'
import TrendBadge from './TrendBadge'

interface AnalyticsRowProps {
  analytics: SeriesAnalytics
}

/**
 * The closed-quarter trend signals for a series, shown above the chart on the
 * drill-down page: a quick read of which way the KPI is moving before the user
 * studies the line.
 *
 * YoY and QoQ are computed from the full history, so they do not change when
 * the period filter narrows the chart. The row sits above that filter to make
 * the independence visible.
 */
export default function AnalyticsRow({ analytics }: AnalyticsRowProps) {
  return (
    <section className="analytics-row" aria-label="Closed-quarter trend">
      <span className="analytics-row-label">Trend</span>
      <TrendBadge
        label="QoQ"
        description="Quarter over quarter"
        value={analytics.qoq}
      />
      <TrendBadge
        label="YoY"
        description="Year over year"
        value={analytics.yoy}
      />
      {analytics.latest_period && (
        <span className="analytics-row-context">
          through {formatPeriod(analytics.latest_period)}
        </span>
      )}
    </section>
  )
}
