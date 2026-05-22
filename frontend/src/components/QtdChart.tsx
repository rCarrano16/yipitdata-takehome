import {
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { QtdPoint } from '../lib/chartData'
import { AXIS_TICK, CHART_RULE, LABEL_INK, SERIES_QTD } from '../lib/chartTheme'
import { formatCompact, formatDate, formatMonthDay, formatValue } from '../lib/format'

interface QtdChartProps {
  data: QtdPoint[]
  unit: string
  /** True when a date filter is active, so the empty-state copy can say so. */
  filtered: boolean
}

/**
 * Panel 2 of the detail view: the quarter-to-date snapshots.
 *
 * This panel has its own Y axis, independent of the history panel. A QTD
 * snapshot of an in-progress quarter is a partial, intra-quarter measure;
 * plotted against closed-quarter totals on a shared axis it collapses into a
 * sliver and reads as a sudden drop. A separate, zero-based scale shows the
 * snapshots clearly. The most recent snapshot is direct-labelled with its
 * value, so the current QTD figure is readable without hovering.
 */
export default function QtdChart({ data, unit, filtered }: QtdChartProps) {
  if (data.length === 0) {
    return (
      <div className="chart-empty">
        {filtered
          ? 'No QTD snapshots in the selected date range. QTD covers Q1 2026.'
          : 'No QTD snapshots for this series yet.'}
      </div>
    )
  }

  const lastIndex = data.length - 1

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 24, right: 56, bottom: 4, left: 8 }}>
        <CartesianGrid stroke={CHART_RULE} vertical={false} />
        <XAxis
          dataKey="asOf"
          interval={0}
          padding={{ left: 12, right: 12 }}
          tick={AXIS_TICK}
          axisLine={{ stroke: CHART_RULE }}
          tickLine={{ stroke: CHART_RULE }}
          tickFormatter={(asOf: string) => formatMonthDay(asOf)}
        />
        <YAxis
          width={64}
          domain={[0, 'auto']}
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
        <Line
          dataKey="value"
          stroke={SERIES_QTD}
          strokeWidth={2}
          dot={{ r: 3 }}
          isAnimationActive={false}
        >
          <LabelList
            position="top"
            offset={10}
            valueAccessor={(_entry, index) =>
              index === lastIndex
                ? formatValue(data[lastIndex].value, unit)
                : ''
            }
            fill={LABEL_INK}
            fontFamily='"Roboto Mono", monospace'
            fontSize={12}
            fontWeight={500}
          />
        </Line>
      </LineChart>
    </ResponsiveContainer>
  )
}
