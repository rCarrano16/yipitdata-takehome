import { describe, expect, it } from 'vitest'
import {
  AVAILABLE_QUARTERS,
  compareQuarters,
  parseQuarter,
  quarterLabel,
  quarterRangeToDates,
} from './quarters'

describe('quarterLabel', () => {
  it('renders a quarter as its YYYYQn label', () => {
    expect(quarterLabel({ year: 2026, quarter: 1 })).toBe('2026Q1')
    expect(quarterLabel({ year: 2024, quarter: 4 })).toBe('2024Q4')
  })
})

describe('parseQuarter', () => {
  it('is the inverse of quarterLabel for every available quarter', () => {
    for (const quarter of AVAILABLE_QUARTERS) {
      expect(parseQuarter(quarterLabel(quarter))).toEqual(quarter)
    }
  })
})

describe('compareQuarters', () => {
  it('orders by year first', () => {
    expect(
      compareQuarters({ year: 2022, quarter: 4 }, { year: 2023, quarter: 1 }),
    ).toBeLessThan(0)
  })

  it('orders by quarter within the same year', () => {
    expect(
      compareQuarters({ year: 2025, quarter: 4 }, { year: 2025, quarter: 2 }),
    ).toBeGreaterThan(0)
  })

  it('returns zero for the same quarter', () => {
    expect(
      compareQuarters({ year: 2024, quarter: 3 }, { year: 2024, quarter: 3 }),
    ).toBe(0)
  })
})

describe('AVAILABLE_QUARTERS', () => {
  it('covers 2022Q1 through 2026Q1 inclusive, 17 quarters', () => {
    expect(AVAILABLE_QUARTERS).toHaveLength(17)
    expect(AVAILABLE_QUARTERS[0]).toEqual({ year: 2022, quarter: 1 })
    expect(AVAILABLE_QUARTERS[16]).toEqual({ year: 2026, quarter: 1 })
  })

  it('is sorted oldest to newest with no gaps', () => {
    for (let i = 1; i < AVAILABLE_QUARTERS.length; i += 1) {
      expect(
        compareQuarters(AVAILABLE_QUARTERS[i - 1], AVAILABLE_QUARTERS[i]),
      ).toBeLessThan(0)
    }
  })
})

describe('quarterRangeToDates', () => {
  it('spans the start quarter first day to the end quarter last day', () => {
    expect(
      quarterRangeToDates({
        from: { year: 2023, quarter: 2 },
        to: { year: 2025, quarter: 4 },
      }),
    ).toEqual({ from: '2023-04-01', to: '2025-12-31' })
  })

  it('handles a single-quarter range', () => {
    expect(
      quarterRangeToDates({
        from: { year: 2026, quarter: 1 },
        to: { year: 2026, quarter: 1 },
      }),
    ).toEqual({ from: '2026-01-01', to: '2026-03-31' })
  })

  it('maps each quarter to its calendar boundaries', () => {
    expect(
      quarterRangeToDates({
        from: { year: 2024, quarter: 3 },
        to: { year: 2024, quarter: 3 },
      }),
    ).toEqual({ from: '2024-07-01', to: '2024-09-30' })
    expect(
      quarterRangeToDates({
        from: { year: 2024, quarter: 2 },
        to: { year: 2024, quarter: 2 },
      }),
    ).toEqual({ from: '2024-04-01', to: '2024-06-30' })
  })
})
