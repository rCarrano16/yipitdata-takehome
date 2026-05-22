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
import type { QtdPoint } from '../lib/chartData'
import {
  AREA_FILL_OPACITY,
  AXIS_TICK,
  CHART_RULE,
  CHART_SURFACE,
  LABEL_INK,
  SERIES_QTD,
} from '../lib/chartTheme'
import {
  formatCompact,
  formatDate,
  formatMonthDay,
  formatValue,
} from '../lib/format'

interface QtdChartProps {
  data: QtdPoint[]
  unit: string
}

/**
 * Panel 2 of the detail view: the quarter-to-date snapshots.
 *
 * This panel has its own zero-based Y axis, independent of the history panel.
 * A QTD snapshot of an in-progress quarter is a partial, intra-quarter measure;
 * plotted against closed-quarter totals on a shared axis it collapses into a
 * sliver and reads as a sudden drop. A separate scale shows the snapshots
 * clearly. The most recent snapshot carries an emphasized dot and a value
 * label, so the current QTD figure is readable without hovering.
 */
export default function QtdChart({ data, unit }: QtdChartProps) {
  if (data.length === 0) {
    return (
      <div className="chart-empty">No QTD snapshots for this series.</div>
    )
  }

  const lastIndex = data.length - 1
  const last = data[lastIndex]

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ top: 24, right: 56, bottom: 4, left: 8 }}>
        <defs>
          <linearGradient id="qtdAreaFill" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="0%"
              stopColor={SERIES_QTD}
              stopOpacity={AREA_FILL_OPACITY}
            />
            <stop offset="100%" stopColor={SERIES_QTD} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={CHART_RULE} vertical={false} />
        <XAxis
          dataKey="asOf"
          interval={0}
          padding={{ left: 12, right: 12 }}
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
          tickFormatter={(asOf: string) => formatMonthDay(asOf)}
        />
        <YAxis
          width={64}
          domain={[0, 'auto']}
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
            // Recharts types the tooltip payload loosely; `payload[0].payload`
            // is the original data row, which here is always a QtdPoint.
            const point = payload[0].payload as QtdPoint
            return (
              <div className="chart-tooltip">
                <div className="chart-tooltip-label">QTD snapshot</div>
                <div className="chart-tooltip-value">
                  {formatValue(point.value, unit)}
                </div>
                <div className="muted">as of {formatDate(point.asOf)}</div>
              </div>
            )
          }}
        />
        <Area
          dataKey="value"
          type="linear"
          stroke={SERIES_QTD}
          strokeWidth={2}
          fill="url(#qtdAreaFill)"
          fillOpacity={1}
          dot={false}
          activeDot={{
            r: 4,
            fill: SERIES_QTD,
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
          x={last.asOf}
          y={last.value}
          r={4.5}
          fill={SERIES_QTD}
          stroke={CHART_SURFACE}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
