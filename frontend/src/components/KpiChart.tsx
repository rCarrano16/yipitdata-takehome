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
import {
  formatCompact,
  formatDate,
  formatPeriod,
  formatQuarterTick,
  formatValue,
} from '../lib/format'

// Recharts takes colors as plain props, and var() does not resolve inside SVG
// presentation attributes, so the design tokens are mirrored here as literal
// constants. Keep these in sync with the tokens in styles.css.
const HISTORICAL_COLOR = '#197f9f' // --series-history
const QTD_COLOR = '#f48c5c' // --series-qtd
const CHROME_COLOR = '#dde5e7' // --rule: grid, axis, and tick lines
const AXIS_TEXT_COLOR = '#616767' // --ink-muted: axis tick labels

// Axis tick text: Roboto Mono, 11px, --ink-muted (design-system section 8).
const AXIS_TICK = {
  fontSize: 11,
  fontFamily: '"Roboto Mono", monospace',
  fill: AXIS_TEXT_COLOR,
}

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
          <CartesianGrid stroke={CHROME_COLOR} vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={['dataMin', 'dataMax']}
            tickCount={8}
            tick={AXIS_TICK}
            axisLine={{ stroke: CHROME_COLOR }}
            tickLine={{ stroke: CHROME_COLOR }}
            tickFormatter={(t: number) => formatQuarterTick(t)}
          />
          <YAxis
            width={64}
            tick={AXIS_TICK}
            axisLine={{ stroke: CHROME_COLOR }}
            tickLine={{ stroke: CHROME_COLOR }}
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
                  <div className="chart-tooltip-value">
                    {formatValue(Number(entry.value), series.unit)}
                  </div>
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
