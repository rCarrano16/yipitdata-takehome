import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { HistoryPoint } from '../lib/chartData'
import { AXIS_TICK, CHART_RULE, SERIES_HISTORY } from '../lib/chartTheme'
import {
  formatCompact,
  formatPeriod,
  formatQuarterTick,
  formatValue,
} from '../lib/format'

interface HistoryChartProps {
  data: HistoryPoint[]
  unit: string
}

/**
 * Panel 1 of the detail view: the closed-quarter history line.
 *
 * The X axis is a continuous time scale, so the quarterly points are spaced by
 * real time. The line covers only closed quarters, so it ends at the most
 * recent closed quarter and never reaches into the in-progress one; the QTD
 * snapshots are drawn separately by `QtdChart`, on their own scale.
 */
export default function HistoryChart({ data, unit }: HistoryChartProps) {
  if (data.length === 0) {
    return (
      <div className="chart-empty">
        No closed quarters in the selected date range.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid stroke={CHART_RULE} vertical={false} />
        <XAxis
          dataKey="t"
          type="number"
          scale="time"
          domain={['dataMin', 'dataMax']}
          tickCount={7}
          tick={AXIS_TICK}
          axisLine={{ stroke: CHART_RULE }}
          tickLine={{ stroke: CHART_RULE }}
          tickFormatter={(t: number) => formatQuarterTick(t)}
        />
        <YAxis
          width={64}
          tick={AXIS_TICK}
          axisLine={{ stroke: CHART_RULE }}
          tickLine={{ stroke: CHART_RULE }}
          tickFormatter={(value: number) => formatCompact(value)}
        />
        <Tooltip
          isAnimationActive={false}
          content={({ active, payload }) => {
            if (!active || !payload || payload.length === 0) {
              return null
            }
            const point = payload[0].payload as HistoryPoint
            return (
              <div className="chart-tooltip">
                <div className="chart-tooltip-label">Closed quarter</div>
                <div className="chart-tooltip-value">
                  {formatValue(point.value, unit)}
                </div>
                <div className="muted">{formatPeriod(point.period)}</div>
              </div>
            )
          }}
        />
        <Line
          dataKey="value"
          stroke={SERIES_HISTORY}
          strokeWidth={2}
          dot={{ r: 2 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
