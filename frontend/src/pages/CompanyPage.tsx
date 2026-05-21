import { Link, useParams } from 'react-router-dom'
import { getCompanyEstimates } from '../api/client'
import type { SeriesDetail } from '../api/types'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import SummaryCard from '../components/SummaryCard'
import { useApi } from '../hooks/useApi'

// The summary card sparkline shows the most recent closed quarters of history.
const SPARKLINE_POINTS = 8

/**
 * Adapt a full SeriesDetail into the primitive props SummaryCard expects. The
 * history is ordered oldest first by the backend, so the last element is the
 * latest closed quarter.
 */
function toCardProps(series: SeriesDetail) {
  const { history } = series
  const latest = history.length > 0 ? history[history.length - 1] : null
  return {
    ticker: series.ticker,
    kpi: series.kpi,
    unit: series.unit,
    latestValue: latest ? latest.value : null,
    latestPeriod: latest ? latest.period : null,
    qtdValue: series.current_qtd ? series.current_qtd.value : null,
    qtdAsOf: series.current_qtd ? series.current_qtd.as_of : null,
    sparkline: history.slice(-SPARKLINE_POINTS).map((point) => point.value),
  }
}

/**
 * One company and every KPI series it reports, each rendered as a summary card
 * linking to the detailed chart. Uses GET /companies/:ticker/estimates, the
 * precise endpoint that returns a 404 for an unknown ticker.
 */
export default function CompanyPage() {
  const { ticker = '' } = useParams()
  const { data, loading, error, reload } = useApi(
    () => getCompanyEstimates(ticker),
    [ticker],
  )

  if (loading && !data) {
    return <LoadingState message="Loading company..." />
  }
  if (error && !data) {
    return <ErrorState message={error.message} onRetry={reload} />
  }
  if (!data) {
    return null
  }

  return (
    <div>
      <Link to="/" className="back-link">
        &larr; Back to directory
      </Link>
      <h1 className="page-title">{data.company_name}</h1>
      <p className="page-subtitle">
        {data.ticker} &middot; {data.sector}
      </p>

      {data.series.length === 0 ? (
        <div className="state">No KPI series for this company.</div>
      ) : (
        <div className="card-grid">
          {data.series.map((series) => (
            <SummaryCard key={series.kpi} {...toCardProps(series)} />
          ))}
        </div>
      )}
    </div>
  )
}
