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
import type { Preset } from '../lib/periodPresets'

/**
 * The drill-down: the two-panel history and QTD chart for one (company, KPI)
 * series, with a period-preset filter, the two timestamps, and CSV export.
 *
 * The period filter is applied server-side: picking a preset re-fetches the
 * series for that date range, so the chart, the timestamps, and the export all
 * read one consistent filtered payload. While a re-fetch is in flight `useApi`
 * keeps the previous data, so the chart stays on screen (dimmed) instead of
 * flashing a spinner. If a re-fetch fails, the last good data stays up under a
 * non-blocking error banner rather than replacing the whole page.
 */
export default function SeriesPage() {
  const { ticker = '', kpi = '' } = useParams()
  const [preset, setPreset] = useState<Preset>('all')
  // Capture "now" once. The preset range, and the useApi deps derived from it,
  // must stay stable across renders so an unrelated render cannot trigger a
  // spurious refetch; only changing the preset should.
  const [now] = useState(() => new Date())
  const { from, to } = computePresetRange(preset, now)

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

      <PeriodFilter selected={preset} onSelect={setPreset} />

      <div className="series-toolbar">
        <TimestampBadge
          lastUpdated={data.last_updated}
          qtdAsOf={data.current_qtd ? data.current_qtd.as_of : null}
          filtered={preset !== 'all'}
        />
        <ExportButton series={data} disabled={isEmpty} />
      </div>

      {/* A re-fetch failed but `useApi` kept the last good data: show it under
          a non-blocking banner instead of a full-page error (review F3). */}
      {error && (
        <div className="error-banner">
          <span>Could not refresh the series: {error.message}</span>
          <button type="button" className="btn" onClick={reload}>
            Retry
          </button>
        </div>
      )}

      <KpiChart series={data} stale={loading} />
    </div>
  )
}
