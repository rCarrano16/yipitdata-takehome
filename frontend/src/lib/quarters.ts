/**
 * Calendar-quarter helpers for the detail chart's custom date filter.
 *
 * The dataset covers a fixed, documented window: 16 closed historical
 * quarters (2022Q1 through 2025Q4) and one in-progress QTD quarter (2026Q1),
 * 17 quarters in all. The custom filter lets the user pick any two of them as
 * a range, which resolves to the `{ from, to }` ISO date pair the existing
 * server-side date filter already accepts (the same shape `computePresetRange`
 * returns).
 *
 * Quarters here are calendar quarters: Q1 is Jan-Mar, Q2 Apr-Jun, Q3 Jul-Sep,
 * Q4 Oct-Dec. None of the four quarter-end dates falls in February, so the
 * start/end lookups below are static and need no leap-year handling.
 */

/** A calendar quarter. `{ year: 2026, quarter: 1 }` is 2026Q1. */
export interface Quarter {
  year: number
  quarter: 1 | 2 | 3 | 4
}

/** An inclusive quarter range, the value the custom filter selects. */
export interface QuarterRange {
  from: Quarter
  to: Quarter
}

/** First and last quarter the dataset covers (docs/assignment-brief.md). */
const FIRST_QUARTER: Quarter = { year: 2022, quarter: 1 }
const LAST_QUARTER: Quarter = { year: 2026, quarter: 1 }

/** Month-day of the first day of each quarter. */
const QUARTER_START: Record<1 | 2 | 3 | 4, string> = {
  1: '01-01',
  2: '04-01',
  3: '07-01',
  4: '10-01',
}

/** Month-day of the last day of each quarter (none in February, all fixed). */
const QUARTER_END: Record<1 | 2 | 3 | 4, string> = {
  1: '03-31',
  2: '06-30',
  3: '09-30',
  4: '12-31',
}

/** Render a quarter as its label, e.g. `2026Q1`. */
export function quarterLabel(quarter: Quarter): string {
  return `${quarter.year}Q${quarter.quarter}`
}

/** Parse a `2026Q1`-style label back into a `Quarter` (inverse of `quarterLabel`). */
export function parseQuarter(label: string): Quarter {
  return {
    year: Number(label.slice(0, 4)),
    quarter: Number(label.slice(5)) as 1 | 2 | 3 | 4,
  }
}

/**
 * Order two quarters: negative if `a` is earlier, positive if later, zero if
 * they are the same quarter. Mirrors the `Array.prototype.sort` comparator
 * contract.
 */
export function compareQuarters(a: Quarter, b: Quarter): number {
  return a.year !== b.year ? a.year - b.year : a.quarter - b.quarter
}

/** The next quarter, rolling Q4 into Q1 of the following year. */
function nextQuarter(quarter: Quarter): Quarter {
  return quarter.quarter === 4
    ? { year: quarter.year + 1, quarter: 1 }
    : { year: quarter.year, quarter: (quarter.quarter + 1) as 1 | 2 | 3 | 4 }
}

/** Build the inclusive list of quarters from `first` to `last`, oldest first. */
function quartersBetween(first: Quarter, last: Quarter): Quarter[] {
  const quarters: Quarter[] = []
  let current = first
  while (compareQuarters(current, last) <= 0) {
    quarters.push(current)
    current = nextQuarter(current)
  }
  return quarters
}

/** Every quarter the dataset covers, oldest first (2022Q1 .. 2026Q1). */
export const AVAILABLE_QUARTERS: Quarter[] = quartersBetween(
  FIRST_QUARTER,
  LAST_QUARTER,
)

/**
 * Resolve an inclusive quarter range to the `{ from, to }` ISO date pair the
 * server-side filter accepts: `from` is the first day of the start quarter,
 * `to` is the last day of the end quarter. The caller must pass `from` no
 * later than `to`; `PeriodFilter` clamps the range before calling this, so no
 * inverted range ever reaches here.
 */
export function quarterRangeToDates(range: QuarterRange): {
  from: string
  to: string
} {
  return {
    from: `${range.from.year}-${QUARTER_START[range.from.quarter]}`,
    to: `${range.to.year}-${QUARTER_END[range.to.quarter]}`,
  }
}
