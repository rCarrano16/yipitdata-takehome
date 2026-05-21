import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getSeries } from '../api/client'
import DateRangeFilter from '../components/DateRangeFilter'
import ErrorState from '../components/ErrorState'
import ExportButton from '../components/ExportButton'
import KpiChart from '../components/KpiChart'
import LoadingState from '../components/LoadingState'
import TimestampBadge from '../components/TimestampBadge'
import { useApi } from '../hooks/useApi'

/**
 * The drill-down: the detailed history-vs-QTD chart for one (company, KPI)
 * series, with a date-range filter, the two timestamps, and CSV export.
 *
 * The date filter is applied server-side: changing it re-fetches the series,
 * so the chart, the timestamps, and the export all read one consistent
 * filtered payload. While a re-fetch is in flight `useApi` keeps the previous
 * data, so the chart stays on screen (dimmed) instead of flashing a spinner.
 * If a re-fetch fails, the last good data stays up under a non-blocking error
 * banner rather than replacing the whole page with a full error state.
 */
export default function SeriesPage() {
  const { ticker = '', kpi = '' } = useParams()
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')

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

      <DateRangeFilter
        from={from}
        to={to}
        onFromChange={setFrom}
        onToChange={setTo}
      />

      <div className="series-toolbar">
        <TimestampBadge
          lastUpdated={data.last_updated}
          qtdAsOf={data.current_qtd ? data.current_qtd.as_of : null}
          filtered={Boolean(from || to)}
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

      <div className={loading ? 'chart-card chart-stale' : 'chart-card'}>
        <KpiChart series={data} />
      </div>
    </div>
  )
}
