interface SparklineProps {
  values: number[]
  width?: number
  height?: number
}

/**
 * A tiny trend line for a summary card. Hand-rolled SVG on purpose: the
 * overview renders up to 100 cards, and a full charting library per card would
 * undercut the fast-glance goal. Recharts is reserved for the one detailed
 * chart on the series page.
 *
 * The viewBox uses the given width and height, but the CSS stretches the SVG
 * to the card width (`preserveAspectRatio="none"`), so the line always spans
 * the card. `vectorEffect` keeps the stroke an even thickness while stretched.
 */
export default function Sparkline({
  values,
  width = 120,
  height = 32,
}: SparklineProps) {
  // Two points are the minimum that draws a line.
  if (values.length < 2) {
    return (
      <svg
        className="sparkline"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        aria-hidden="true"
      />
    )
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  // A flat series has a zero range; fall back to 1 to avoid dividing by zero.
  const range = max - min || 1
  const stepX = width / (values.length - 1)
  const pad = 2

  const points = values
    .map((value, index) => {
      const x = index * stepX
      // SVG y grows downward, so the highest value maps to the smallest y.
      const y = pad + (1 - (value - min) / range) * (height - 2 * pad)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')

  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <polyline points={points} vectorEffect="non-scaling-stroke" />
    </svg>
  )
}
