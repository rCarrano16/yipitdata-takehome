import {
  Area,
  AreaChart,
  CartesianGrid,
  LabelList,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { HistoryPoint } from '../lib/chartData'
import {
  AREA_FILL_OPACITY,
  AXIS_TICK,
  CHART_RULE,
  CHART_SURFACE,
  LABEL_INK,
  SERIES_HISTORY,
} from '../lib/chartTheme'
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
 * Panel 1 of the detail view: the closed-quarter history.
 *
 * The X axis plots epoch milliseconds, so the quarterly points are spaced by
 * real time. The series covers only closed quarters, so it ends at the most
 * recent closed quarter; the QTD snapshots are drawn separately by `QtdChart`.
 * The latest closed quarter carries an emphasized dot and a value label.
 */
export default function HistoryChart({ data, unit }: HistoryChartProps) {
  if (data.length === 0) {
    return (
      <div className="chart-empty">No closed quarters for this series.</div>
    )
  }

  const lastIndex = data.length - 1
  const last = data[lastIndex]

  // Thin the X-axis ticks: show every quarter when there are few, otherwise
  // keep every `step`-th one (so the kept ticks stay evenly spaced) for at
  // most ~7 ticks. Without explicit ticks Recharts labels all 16 quarters and
  // the date labels collide.
  const step = Math.ceil(data.length / 7)
  const tickValues = data
    .filter((_, index) => index % step === 0)
    .map((point) => point.t)

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ top: 24, right: 52, bottom: 4, left: 8 }}>
        <defs>
          <linearGradient id="historyAreaFill" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="0%"
              stopColor={SERIES_HISTORY}
              stopOpacity={AREA_FILL_OPACITY}
            />
            <stop offset="100%" stopColor={SERIES_HISTORY} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={CHART_RULE} vertical={false} />
        <XAxis
          dataKey="t"
          type="number"
          domain={['dataMin', 'dataMax']}
          ticks={tickValues}
          interval={0}
          padding={{ left: 12, right: 12 }}
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
          tickFormatter={(t: number) => formatQuarterTick(t)}
        />
        <YAxis
          width={64}
          tickCount={4}
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
          tickFormatter={(value: number) => formatCompact(value)}
        />
        <Tooltip
          isAnimationActive={false}
          cursor={{ stroke: CHART_RULE, strokeWidth: 1 }}
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
        <Area
          dataKey="value"
          type="linear"
          stroke={SERIES_HISTORY}
          strokeWidth={2}
          fill="url(#historyAreaFill)"
          fillOpacity={1}
          dot={false}
          activeDot={{
            r: 4,
            fill: SERIES_HISTORY,
            stroke: CHART_SURFACE,
            strokeWidth: 2,
          }}
          isAnimationActive={false}
        >
          <LabelList
            position="top"
            offset={10}
            valueAccessor={(_entry, index) =>
              index === lastIndex ? formatValue(last.value, unit) : ''
            }
            fill={LABEL_INK}
            fontFamily='"Roboto Mono", monospace'
            fontSize={12}
            fontWeight={500}
          />
        </Area>
        <ReferenceDot
          x={last.t}
          y={last.value}
          r={4.5}
          fill={SERIES_HISTORY}
          stroke={CHART_SURFACE}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
