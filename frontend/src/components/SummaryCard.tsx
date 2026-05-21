import { Link } from 'react-router-dom'
import { formatDate, formatPeriod, formatValue } from '../lib/format'
import Sparkline from './Sparkline'

interface SummaryCardProps {
  ticker: string
  kpi: string
  unit: string
  latestValue: number | null
  latestPeriod: string | null
  qtdValue: number | null
  qtdAsOf: string | null
  sparkline: number[]
}

/**
 * One glanceable card for a (company, KPI) series: the latest closed-quarter
 * value, a sparkline of recent history, and the current QTD value with its
 * as-of date. The whole card links to the detailed series page.
 *
 * The props are primitives, not a backend type, so both the overview (from an
 * OverviewCard) and the company page (from a SeriesDetail) feed this one
 * component through a small adapter.
 */
export default function SummaryCard({
  ticker,
  kpi,
  unit,
  latestValue,
  latestPeriod,
  qtdValue,
  qtdAsOf,
  sparkline,
}: SummaryCardProps) {
  // encodeURIComponent is required: KPI names contain spaces and parentheses.
  const to = `/companies/${encodeURIComponent(ticker)}/kpis/${encodeURIComponent(kpi)}`

  return (
    <Link to={to} className="card">
      <div className="card-kpi">{kpi}</div>
      <div className="card-value">
        {latestValue !== null ? formatValue(latestValue, unit) : 'n/a'}
      </div>
      <div className="card-period">
        {latestPeriod
          ? `Latest closed: ${formatPeriod(latestPeriod)}`
          : 'No closed history'}
      </div>

      {sparkline.length >= 2 && (
        <div className="card-sparkline">
          <Sparkline values={sparkline} />
        </div>
      )}

      <div className="card-qtd">
        <span className="muted">Current QTD</span>
        <span className="card-qtd-value">
          {qtdValue !== null ? formatValue(qtdValue, unit) : 'n/a'}
        </span>
      </div>
      {qtdAsOf && <div className="badge">as of {formatDate(qtdAsOf)}</div>}
    </Link>
  )
}
