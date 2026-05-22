import { Link } from 'react-router-dom'
import {
  formatDate,
  formatPeriod,
  formatValue,
  formatValueParts,
} from '../lib/format'
import Sparkline from './Sparkline'
import TrendBadge from './TrendBadge'

interface SummaryCardProps {
  ticker: string
  kpi: string
  unit: string
  latestValue: number | null
  latestPeriod: string | null
  qoq: number | null
  yoy: number | null
  qtdValue: number | null
  qtdAsOf: string | null
  sparkline: number[]
}

/**
 * One glanceable card for a (company, KPI) series: the latest closed-quarter
 * value, a sparkline of recent history, and the current QTD value with its
 * as-of date. The whole card links to the detailed series page.
 *
 * The props are primitives, not a backend type, so the company page can feed
 * this component from a SeriesDetail through a small adapter.
 */
export default function SummaryCard({
  ticker,
  kpi,
  unit,
  latestValue,
  latestPeriod,
  qoq,
  yoy,
  qtdValue,
  qtdAsOf,
  sparkline,
}: SummaryCardProps) {
  // encodeURIComponent is required: KPI names contain spaces and parentheses.
  const to = `/companies/${encodeURIComponent(ticker)}/kpis/${encodeURIComponent(kpi)}`

  // The hero figure and its unit render as separate elements so the 30px
  // monospaced number stays the focus and the unit reads as a quiet label.
  const hero = latestValue !== null ? formatValueParts(latestValue, unit) : null

  return (
    <Link to={to} className="card">
      <div className="card-kpi">{kpi}</div>
      <div className="card-value">
        <span className="card-figure">{hero ? hero.figure : 'n/a'}</span>
        {hero && hero.unitLabel && (
          <span className="card-unit">{hero.unitLabel}</span>
        )}
      </div>
      <div className="card-period">
        {latestPeriod
          ? `Latest closed: ${formatPeriod(latestPeriod)}`
          : 'No closed history'}
      </div>

      {latestPeriod && (
        <div className="card-trend">
          <TrendBadge
            label="QoQ"
            description="Quarter over quarter"
            value={qoq}
          />
          <TrendBadge label="YoY" description="Year over year" value={yoy} />
        </div>
      )}

      {sparkline.length >= 2 && (
        <div className="card-sparkline">
          <Sparkline values={sparkline} />
        </div>
      )}

      <div className="card-qtd">
        <div className="card-qtd-row">
          <span className="card-qtd-label">Current QTD</span>
          <span className="card-qtd-value">
            {qtdValue !== null ? formatValue(qtdValue, unit) : 'n/a'}
          </span>
        </div>
        {qtdAsOf && <div className="badge">as of {formatDate(qtdAsOf)}</div>}
      </div>
    </Link>
  )
}
