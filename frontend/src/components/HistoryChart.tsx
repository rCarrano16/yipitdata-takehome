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
import type { Preset } from '../lib/periodPresets'

interface HistoryChartProps {
  data: HistoryPoint[]
  unit: string
  preset: Preset
}

/**
 * Panel 1 of the detail view: the closed-quarter history.
 *
 * The X axis is a continuous time scale, so the quarterly points are spaced by
 * real time. The series covers only closed quarters, so it ends at the most
 * recent closed quarter; the QTD snapshots are drawn separately by `QtdChart`.
 * The latest closed quarter carries an emphasized dot and a value label.
 */
export default function HistoryChart({
  data,
  unit,
  preset,
}: HistoryChartProps) {
  if (data.length === 0) {
    return (
      <div className="chart-empty">
        {preset === 'ytd'
          ? 'No closed quarters in 2026 yet. See quarter-to-date.'
          : 'No closed quarters in the selected period.'}
      </div>
    )
  }

  const lastIndex = data.length - 1
  const last = data[lastIndex]

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
          scale="time"
          domain={['dataMin', 'dataMax']}
          tickCount={7}
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
