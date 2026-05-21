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
 * Format a value for its unit. The five KPIs use four units: `$` (a price,
 * two decimals), `$MM` (revenue in millions, one decimal), and `subs` /
 * `units` (whole counts).
 */
export function formatValue(value: number, unit: string): string {
  switch (unit) {
    case '$':
      return `$${formatNumber(value, 2)}`
    case '$MM':
      return `$${formatNumber(value, 1)} MM`
    case 'subs':
      return `${formatNumber(value, 0)} subs`
    case 'units':
      return `${formatNumber(value, 0)} units`
    default:
      return `${formatNumber(value, 2)} ${unit}`
  }
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
