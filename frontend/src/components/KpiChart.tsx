import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SeriesDetail } from '../api/types'
import type { ChartPoint } from '../lib/chartData'
import { toChartData } from '../lib/chartData'
import { formatCompact, formatDate, formatPeriod, formatValue } from '../lib/format'

// These match --accent and --qtd in styles.css. Recharts takes colors as
// props, so they are kept here as plain constants.
const HISTORICAL_COLOR = '#2563eb'
const QTD_COLOR = '#d97706'

interface KpiChartProps {
  series: SeriesDetail
}

/**
 * The detailed history-vs-QTD chart.
 *
 * The X axis is a continuous time scale, not a category axis, so the 16
 * quarterly history points are spaced by real time and the four QTD snapshots
 * sit clustered at the right edge. The two `<Line>` series read different
 * data keys and use `connectNulls={false}`, so they draw as two separate,
 * unconnected lines: a solid line for closed history, a dashed line for the
 * in-progress quarter.
 */
export default function KpiChart({ series }: KpiChartProps) {
  const data = toChartData(series)

  if (data.length === 0) {
    return (
      <div className="chart-empty">No data points in the selected range.</div>
    )
  }

  return (
    <>
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={data} margin={{ top: 8, right: 24, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="#eef0f3" />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={['dataMin', 'dataMax']}
            tick={{ fontSize: 12 }}
            tickFormatter={(t: number) =>
              new Date(t).toLocaleDateString('en-US', {
                month: 'short',
                year: 'numeric',
              })
            }
          />
          <YAxis
            width={64}
            tick={{ fontSize: 12 }}
            tickFormatter={(value: number) => formatCompact(value)}
          />
          <Tooltip
            isAnimationActive={false}
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) {
                return null
              }
              // The hovered x carries an entry for each line; the line that is
              // null there has a null value, so keep the one real point.
              const entry = payload.find((item) => item.value != null)
              if (!entry || entry.value == null) {
                return null
              }
              const point = entry.payload as ChartPoint
              const isQtd = entry.dataKey === 'qtd'
              return (
                <div className="chart-tooltip">
                  <div className="chart-tooltip-label">
                    {isQtd ? 'QTD snapshot' : 'Closed quarter'}
                  </div>
                  <div>{formatValue(Number(entry.value), series.unit)}</div>
                  <div className="muted">
                    {isQtd && point.asOf
                      ? `as of ${formatDate(point.asOf)}`
                      : formatPeriod(point.period)}
                  </div>
                </div>
              )
            }}
          />
          <Line
            name="Historical"
            dataKey="historical"
            stroke={HISTORICAL_COLOR}
            strokeWidth={2}
            dot={{ r: 2 }}
            connectNulls={false}
            isAnimationActive={false}
          />
          <Line
            name="QTD"
            dataKey="qtd"
            stroke={QTD_COLOR}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={{ r: 3 }}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="legend">
        <span className="legend-item">
          <span
            className="legend-swatch"
            style={{ background: HISTORICAL_COLOR }}
          />
          Closed-quarter history
        </span>
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: QTD_COLOR }} />
          QTD snapshots
        </span>
      </div>
    </>
  )
}
