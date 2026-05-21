/**
 * Formatting helpers: the single place a raw value or an ISO date string is
 * turned into display text. Summary cards, the chart axes and tooltips, and
 * the CSV export all go through here, so formatting stays consistent.
 */

function formatNumber(value: number, decimals: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * Split a value into the figure shown large on a card (the number, with any
 * currency prefix) and the unit word shown small beside it. A summary card
 * renders the figure as a 30px monospaced hero and the unit as a quiet label,
 * so a long value such as "66,151,925 units" never crowds the figure.
 */
export function formatValueParts(
  value: number,
  unit: string,
): { figure: string; unitLabel: string } {
  switch (unit) {
    case '$':
      return { figure: `$${formatNumber(value, 2)}`, unitLabel: '' }
    case '$MM':
      return { figure: `$${formatNumber(value, 1)}`, unitLabel: 'MM' }
    case 'subs':
      return { figure: formatNumber(value, 0), unitLabel: 'subs' }
    case 'units':
      return { figure: formatNumber(value, 0), unitLabel: 'units' }
    default:
      return { figure: formatNumber(value, 2), unitLabel: unit }
  }
}

/**
 * Format a value for its unit as a single string. The five KPIs use four
 * units: `$` (a price, two decimals), `$MM` (revenue in millions, one
 * decimal), and `subs` / `units` (whole counts). Chart tooltips, the QTD value,
 * and the CSV export use this combined form; the card hero uses the split
 * `formatValueParts`.
 */
export function formatValue(value: number, unit: string): string {
  const { figure, unitLabel } = formatValueParts(value, unit)
  return unitLabel ? `${figure} ${unitLabel}` : figure
}

/** A short value for a chart axis tick, e.g. 1_200_000 -> "1.2M". */
export function formatCompact(value: number): string {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

/** Turn a period code into a readable label, e.g. "2026Q1" -> "Q1 2026". */
export function formatPeriod(period: string): string {
  const match = period.match(/^(\d{4})Q([1-4])$/)
  return match ? `Q${match[2]} ${match[1]}` : period
}

/**
 * Format an epoch-millis timestamp as a short quarter label for a chart axis
 * tick, e.g. "Q1 '24". The detailed chart's X axis is a time scale, so a tick
 * can land on any date; the label always reports the quarter that date is in.
 */
export function formatQuarterTick(t: number): string {
  const d = new Date(t)
  const quarter = Math.floor(d.getMonth() / 3) + 1
  const year = String(d.getFullYear()).slice(-2)
  return `Q${quarter} '${year}`
}

/**
 * Parse an ISO string into a Date. A date-only string ("YYYY-MM-DD") is given
 * a local-midnight time, so the displayed day never shifts by a time zone. A
 * full datetime carries its own offset and is parsed as-is.
 */
export function parseDate(iso: string): Date | null {
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso)
  return Number.isNaN(d.getTime()) ? null : d
}

/** Format a date string as "Mar 31, 2025". Falls back to the raw input. */
export function formatDate(iso: string): string {
  const d = parseDate(iso)
  return d
    ? d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : iso
}

/** Format a datetime string as "May 21, 2026, 02:30 PM". Falls back to raw. */
export function formatDateTime(iso: string): string {
  const d = parseDate(iso)
  return d
    ? d.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : iso
}
