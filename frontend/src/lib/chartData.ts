/**
 * The transforms behind the detail chart. The drill-down renders two separate
 * panels, one for closed-quarter history and one for the quarter-to-date
 * snapshots, each on its own scale, so the data is shaped into two independent
 * arrays rather than one merged series.
 *
 * History points are plotted at their `period_end` on a continuous time axis;
 * QTD points are plotted at their `as_of` snapshot date.
 */

import type { SeriesDetail } from '../api/types'
import { parseDate } from './format'

/** One closed-quarter point on the history panel. */
export interface HistoryPoint {
  /** Epoch milliseconds of `period_end`: the numeric time X-axis value. */
  t: number
  /** The closed-quarter estimate value. */
  value: number
  /** The quarter code, e.g. "2025Q4", shown in the tooltip. */
  period: string
}

/** One intra-quarter snapshot on the quarter-to-date panel. */
export interface QtdPoint {
  /** The snapshot date "YYYY-MM-DD": the category X-axis value. */
  asOf: string
  /** The QTD estimate value at this snapshot. */
  value: number
  /** The quarter code, e.g. "2026Q1". */
  period: string
}

/** Closed-quarter history as a time-sorted array for the history panel. */
export function toHistorySeries(series: SeriesDetail): HistoryPoint[] {
  const points: HistoryPoint[] = []

  for (const point of series.history) {
    const t = parseDate(point.period_end)?.getTime()
    if (t === undefined) continue
    points.push({ t, value: point.value, period: point.period })
  }

  points.sort((a, b) => a.t - b.t)
  return points
}

/**
 * The percent change across a panel's points, first to last, as a fraction
 * (0.05 means +5%). Returns null when there are fewer than two points or the
 * first value is zero (a change off a zero base is undefined).
 *
 * Unlike the YoY/QoQ analytics, this moves with the chart's date filter: it
 * summarizes exactly the range currently on screen. Both HistoryPoint and
 * QtdPoint carry a `value`, so one helper serves both panels.
 */
export function rangeChange(points: { value: number }[]): number | null {
  if (points.length < 2) return null
  const first = points[0].value
  const last = points[points.length - 1].value
  if (first === 0) return null
  return (last - first) / first
}

/** QTD snapshots as an as_of-sorted array for the quarter-to-date panel. */
export function toQtdSeries(series: SeriesDetail): QtdPoint[] {
  const points: QtdPoint[] = []

  for (const snapshot of series.qtd_snapshots) {
    if (parseDate(snapshot.as_of) === null) continue
    points.push({
      asOf: snapshot.as_of,
      value: snapshot.value,
      period: snapshot.period,
    })
  }

  // ISO date strings sort correctly lexically.
  points.sort((a, b) => a.asOf.localeCompare(b.asOf))
  return points
}
