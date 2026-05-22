/**
 * Fiscal-period presets for the detail chart's time filter.
 *
 * Each preset resolves to a `{ from, to }` ISO date pair that drives the
 * existing server-side date filter on the series fetch. "All" is the default
 * and applies no filter (the full available range).
 */

/** A selectable time window for the detail chart. */
export type Preset = 'ytd' | '1y' | '2y' | 'all'

/** The presets in display order, used to render the segmented control. */
export const PERIOD_PRESETS: { value: Preset; label: string }[] = [
  { value: 'ytd', label: 'YTD' },
  { value: '1y', label: '1Y' },
  { value: '2y', label: '2Y' },
  { value: 'all', label: 'All' },
]

/** Format a Date as a local "YYYY-MM-DD" string (no UTC shift). */
function toIsoDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Resolve a preset to the `{ from, to }` date range it selects, relative to
 * `now`. "All" returns empty strings, meaning no filter. The others end at
 * `now`; "YTD" starts on January 1 of the current year, "1Y" and "2Y" start
 * one or two calendar years before `now`. Passing `now` in keeps this pure and
 * testable. The `new Date(year, month, day)` form normalizes an invalid day
 * (a Feb 29 one year back becomes Mar 1), so there is no leap-year gap.
 */
export function computePresetRange(
  preset: Preset,
  now: Date,
): { from: string; to: string } {
  const today = toIsoDate(now)
  switch (preset) {
    case 'all':
      return { from: '', to: '' }
    case 'ytd':
      return { from: `${now.getFullYear()}-01-01`, to: today }
    case '1y':
      return {
        from: toIsoDate(
          new Date(now.getFullYear() - 1, now.getMonth(), now.getDate()),
        ),
        to: today,
      }
    case '2y':
      return {
        from: toIsoDate(
          new Date(now.getFullYear() - 2, now.getMonth(), now.getDate()),
        ),
        to: today,
      }
  }
}
