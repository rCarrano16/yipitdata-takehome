import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getSeries } from '../api/client'
import AnalyticsRow from '../components/AnalyticsRow'
import ErrorState from '../components/ErrorState'
import ExportButton from '../components/ExportButton'
import KpiChart from '../components/KpiChart'
import LoadingState from '../components/LoadingState'
import PeriodFilter from '../components/PeriodFilter'
import TimestampBadge from '../components/TimestampBadge'
import { useApi } from '../hooks/useApi'
import { computePresetRange } from '../lib/periodPresets'
import type { FilterMode } from '../lib/periodPresets'
import { AVAILABLE_QUARTERS, quarterRangeToDates } from '../lib/quarters'
import type { QuarterRange } from '../lib/quarters'

/**
 * The drill-down: the two-panel history and QTD chart for one (company, KPI)
 * series, with a period filter (presets or a custom quarter range), the two
 * timestamps, and CSV export.
 *
 * The period filter is applied server-side: changing it re-fetches the series
 * for that date range, so the chart, the timestamps, and the export all read
 * one consistent filtered payload. While a re-fetch is in flight `useApi`
 * keeps the previous data, so the chart stays on screen (dimmed) instead of
 * flashing a spinner. If a re-fetch fails, the last good data stays up under a
 * non-blocking error banner rather than replacing the whole page.
 */
export default function SeriesPage() {
  const { ticker = '', kpi = '' } = useParams()
  const [mode, setMode] = useState<FilterMode>('all')
  // The custom range defaults to the full dataset window; the user narrows it
  // from there, so switching to "Custom" shows everything until changed.
  const [customRange, setCustomRange] = useState<QuarterRange>(() => ({
    from: AVAILABLE_QUARTERS[0],
    to: AVAILABLE_QUARTERS[AVAILABLE_QUARTERS.length - 1],
  }))
  // Capture "now" once. The resolved date range, and the useApi deps derived
  // from it, must stay stable across renders so an unrelated render cannot
  // trigger a spurious refetch; only changing the mode or the custom range
  // should.
  const [now] = useState(() => new Date())
  const { from, to } =
    mode === 'custom'
      ? quarterRangeToDates(customRange)
      : computePresetRange(mode, now)

  const { data, loading, error, reload } = useApi(
    () => getSeries(ticker, kpi, from || undefined, to || undefined),
    [ticker, kpi, from, to],
  )

  if (loading && !data) {
    return <LoadingState message="Loading series..." />
  }
  if (error && !data) {
    return <ErrorState message={error.message} onRetry={reload} />
  }
  if (!data) {
    return null
  }

  const isEmpty =
    data.history.length === 0 && data.qtd_snapshots.length === 0

  return (
    <div>
      <Link
        to={`/companies/${encodeURIComponent(ticker)}`}
        className="back-link"
      >
        &larr; Back to {data.company_name}
      </Link>

      <div className="series-head">
        <h1 className="page-title">{data.kpi}</h1>
        <p className="page-subtitle">
          {data.company_name} ({data.ticker}) &middot; measured in {data.unit}
        </p>
      </div>

      {/* The trend signals come from the full history, so the row sits above
          the period filter: narrowing the chart does not change them. */}
      {data.analytics.latest_period && (
        <AnalyticsRow analytics={data.analytics} />
      )}

      <PeriodFilter
        selected={mode}
        onSelect={setMode}
        customRange={customRange}
        onCustomRangeChange={setCustomRange}
      />

      <div className="series-toolbar">
        <TimestampBadge
          lastUpdated={data.last_updated}
          qtdAsOf={data.current_qtd ? data.current_qtd.as_of : null}
          filtered={mode !== 'all'}
        />
        <ExportButton series={data} disabled={isEmpty || error !== null} />
      </div>

      {/* A re-fetch failed but `useApi` kept the last good data: show it under
          a non-blocking banner instead of a full-page error (review F3).
          Export is disabled while this banner is up, because the chart shows
          the last successful load, not the filter the controls now describe. */}
      {error && (
        <div className="error-banner">
          <span>
            The latest filter change could not be applied, so the chart and
            export still show the data from the last successful load. Retry to
            apply the current filter. ({error.message})
          </span>
          <button type="button" className="btn" onClick={reload}>
            Retry
          </button>
        </div>
      )}

      <KpiChart series={data} stale={loading} />
    </div>
  )
}
