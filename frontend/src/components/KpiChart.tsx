import type { SeriesDetail } from '../api/types'
import { toHistorySeries, toQtdSeries } from '../lib/chartData'
import { formatPeriod } from '../lib/format'
import type { Preset } from '../lib/periodPresets'
import HistoryChart from './HistoryChart'
import QtdChart from './QtdChart'

interface KpiChartProps {
  series: SeriesDetail
  /** True while a re-fetch is in flight, so both panels dim together. */
  stale: boolean
  /** The active period preset; each panel uses it for its empty-state copy. */
  preset: Preset
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
export default function KpiChart({ series, stale, preset }: KpiChartProps) {
  const history = toHistorySeries(series)
  const qtd = toQtdSeries(series)

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
        <h2 className="chart-panel-title">Quarterly history</h2>
        <p className="chart-panel-scale">{historyScale}</p>
        <HistoryChart data={history} unit={series.unit} preset={preset} />
      </section>
      <section className="chart-panel chart-panel--qtd">
        <h2 className="chart-panel-title">Quarter-to-date</h2>
        <p className="chart-panel-scale">{qtdScale}</p>
        <QtdChart data={qtd} unit={series.unit} preset={preset} />
      </section>
    </div>
  )
}
