import type { SeriesDetail } from '../api/types'
import { rangeChange, toHistorySeries, toQtdSeries } from '../lib/chartData'
import { formatPercent, formatPeriod } from '../lib/format'
import HistoryChart from './HistoryChart'
import QtdChart from './QtdChart'
import TrendValue from './TrendValue'

interface KpiChartProps {
  series: SeriesDetail
  /** True while a re-fetch is in flight, so both panels dim together. */
  stale: boolean
}

/**
 * The detail view: two side-by-side panels, each on its own scale.
 *
 * Closed-quarter history and the quarter-to-date snapshots are two different
 * comparisons. A multi-year trend and the evolution of an estimate inside one
 * in-progress quarter do not belong on a shared axis: an intra-quarter snapshot
 * is a partial measure, so against closed-quarter totals it collapses into a
 * sliver and the history-to-QTD step reads as a sudden drop. Each comparison
 * gets its own titled panel with its own labelled scale.
 */
export default function KpiChart({ series, stale }: KpiChartProps) {
  const history = toHistorySeries(series)
  const qtd = toQtdSeries(series)

  // The change across exactly the points each panel shows. It moves with the
  // period filter on the history panel; the QTD panel always holds the full
  // quarter, so its change is the intra-quarter movement of the estimate.
  const historyChange = rangeChange(history)
  const qtdChange = rangeChange(qtd)

  const historyScale =
    history.length > 0
      ? `Closed quarters, ${formatPeriod(
          history[0].period,
        )} to ${formatPeriod(history[history.length - 1].period)}`
      : 'Closed quarters'
  const qtdScale =
    qtd.length > 0
      ? `${formatPeriod(qtd[0].period)} snapshots, independent scale`
      : 'Snapshots, independent scale'

  return (
    <div className={stale ? 'chart-panels chart-stale' : 'chart-panels'}>
      <section className="chart-panel chart-panel--history">
        <div className="chart-panel-head">
          <h2 className="chart-panel-title">Quarterly history</h2>
          {historyChange !== null && (
            <span
              className="chart-panel-delta"
              aria-label={`Change across the quarters shown: ${formatPercent(
                historyChange,
              )}`}
            >
              <TrendValue value={historyChange} />
            </span>
          )}
        </div>
        <p className="chart-panel-scale">{historyScale}</p>
        <HistoryChart data={history} unit={series.unit} />
      </section>
      <section className="chart-panel chart-panel--qtd">
        <div className="chart-panel-head">
          <h2 className="chart-panel-title">Quarter-to-date</h2>
          {qtdChange !== null && (
            <span
              className="chart-panel-delta"
              aria-label={`Change across the snapshots shown: ${formatPercent(
                qtdChange,
              )}`}
            >
              <TrendValue value={qtdChange} />
            </span>
          )}
        </div>
        <p className="chart-panel-scale">{qtdScale}</p>
        <QtdChart data={qtd} unit={series.unit} />
      </section>
    </div>
  )
}
