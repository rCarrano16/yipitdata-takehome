/**
 * The transform behind the detailed chart: it merges a series' closed-quarter
 * history and its QTD snapshots into one array on a single time axis.
 *
 * Historical points are plotted at their `period_end`, QTD snapshots at their
 * `as_of`. Each row carries the value for only one of the two series (the
 * other is null), so the chart draws two separate, unconnected lines. The
 * array is sorted by time, which a numeric Recharts axis requires.
 */

import type { SeriesDetail } from '../api/types'
import { parseDate } from './format'

export interface ChartPoint {
  /** Epoch milliseconds: the numeric X-axis value. */
  t: number
  /** The historical value at this time, or null on a QTD row. */
  historical: number | null
  /** The QTD value at this time, or null on a historical row. */
  qtd: number | null
  /** The quarter code, e.g. "2025Q4". Present on every row. */
  period: string
  /** The snapshot date, set only on a QTD row. */
  asOf: string | null
}

/** Merge a series into the sorted, single-axis data the chart renders. */
export function toChartData(series: SeriesDetail): ChartPoint[] {
  const points: ChartPoint[] = []

  for (const point of series.history) {
    const t = parseDate(point.period_end)?.getTime()
    if (t === undefined) continue
    points.push({
      t,
      historical: point.value,
      qtd: null,
      period: point.period,
      asOf: null,
    })
  }

  for (const snapshot of series.qtd_snapshots) {
    const t = parseDate(snapshot.as_of)?.getTime()
    if (t === undefined) continue
    points.push({
      t,
      historical: null,
      qtd: snapshot.value,
      period: snapshot.period,
      asOf: snapshot.as_of,
    })
  }

  points.sort((a, b) => a.t - b.t)
  return points
}
