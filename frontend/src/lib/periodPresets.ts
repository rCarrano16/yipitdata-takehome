/**
 * Fiscal-period presets for the detail chart's time filter.
 *
 * Each preset resolves to a `{ from, to }` ISO date pair that drives the
 * existing server-side date filter on the series fetch. "All" is the default
 * and applies no filter (the full available range).
 */

/** A selectable time window for the detail chart. */
export type Preset = 'all' | '3y' | '2y' | '1y'

/** The presets in display order, used to render the segmented control. */
export const PERIOD_PRESETS: { value: Preset; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: '3y', label: '3Y' },
  { value: '2y', label: '2Y' },
  { value: '1y', label: '1Y' },
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
 * `now`. "All" returns empty strings, meaning no filter. "1Y", "2Y", and "3Y"
 * end at `now` and start one, two, or three calendar years before it. Passing
 * `now` in keeps this pure and testable. The `new Date(year, month, day)` form
 * normalizes an invalid day (a Feb 29 some years back becomes Mar 1), so there
 * is no leap-year gap.
 */
export function computePresetRange(
  preset: Preset,
  now: Date,
): { from: string; to: string } {
  const today = toIsoDate(now)
  const yearsBack = (years: number): string =>
    toIsoDate(
      new Date(now.getFullYear() - years, now.getMonth(), now.getDate()),
    )
  switch (preset) {
    case 'all':
      return { from: '', to: '' }
    case '3y':
      return { from: yearsBack(3), to: today }
    case '2y':
      return { from: yearsBack(2), to: today }
    case '1y':
      return { from: yearsBack(1), to: today }
  }
}
