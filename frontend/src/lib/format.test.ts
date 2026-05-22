import { describe, expect, it } from 'vitest'
import {
  formatCompact,
  formatDate,
  formatMonthDay,
  formatPercent,
  formatPeriod,
  formatQuarterTick,
  formatValue,
  formatValueParts,
  parseDate,
  trendTone,
} from './format'

describe('formatValue', () => {
  it('formats a dollar price with two decimals', () => {
    expect(formatValue(1250.756, '$')).toBe('$1,250.76')
  })

  it('formats millions with one decimal and a suffix', () => {
    expect(formatValue(1234.5, '$MM')).toBe('$1,234.5 MM')
  })

  it('formats subscriber counts as whole numbers', () => {
    expect(formatValue(1000000, 'subs')).toBe('1,000,000 subs')
  })

  it('formats unit counts as whole numbers', () => {
    expect(formatValue(42, 'units')).toBe('42 units')
  })

  it('falls back to two decimals plus the unit for an unknown unit', () => {
    expect(formatValue(10, 'widgets')).toBe('10.00 widgets')
  })
})

describe('formatValueParts', () => {
  it('keeps a dollar price whole, with no unit word', () => {
    expect(formatValueParts(404.06, '$')).toEqual({
      figure: '$404.06',
      unitLabel: '',
    })
  })

  it('splits millions into a figure and an MM label', () => {
    expect(formatValueParts(1508.28, '$MM')).toEqual({
      figure: '$1,508.3',
      unitLabel: 'MM',
    })
  })

  it('splits a large count into a figure and its unit word', () => {
    expect(formatValueParts(66151925, 'units')).toEqual({
      figure: '66,151,925',
      unitLabel: 'units',
    })
  })

  it('rejoins to the same string formatValue returns', () => {
    const { figure, unitLabel } = formatValueParts(1000000, 'subs')
    expect(`${figure} ${unitLabel}`).toBe(formatValue(1000000, 'subs'))
  })
})

describe('formatPercent', () => {
  it('formats a rise with an explicit plus sign', () => {
    expect(formatPercent(0.0833)).toBe('+8.3%')
  })

  it('formats a fall with a minus sign', () => {
    expect(formatPercent(-0.12)).toBe('-12.0%')
  })

  it('formats a flat change without a sign', () => {
    expect(formatPercent(0)).toBe('0.0%')
  })

  it('rounds to one decimal place', () => {
    expect(formatPercent(0.23306)).toBe('+23.3%')
  })
})

describe('trendTone', () => {
  it('classifies a rise as positive', () => {
    expect(trendTone(0.1)).toBe('positive')
  })

  it('classifies a fall as negative', () => {
    expect(trendTone(-0.1)).toBe('negative')
  })

  it('treats zero and null as neutral', () => {
    expect(trendTone(0)).toBe('neutral')
    expect(trendTone(null)).toBe('neutral')
  })
})

describe('formatCompact', () => {
  it('shortens large numbers', () => {
    expect(formatCompact(1200000)).toBe('1.2M')
    expect(formatCompact(340000)).toBe('340K')
  })
})

describe('formatPeriod', () => {
  it('turns a period code into a readable label', () => {
    expect(formatPeriod('2026Q1')).toBe('Q1 2026')
  })

  it('passes through a value it does not recognize', () => {
    expect(formatPeriod('unknown')).toBe('unknown')
  })
})

describe('formatQuarterTick', () => {
  it('labels a timestamp with its quarter and two-digit year', () => {
    expect(
      formatQuarterTick(new Date('2024-02-15T00:00:00').getTime()),
    ).toBe("Q1 '24")
    expect(
      formatQuarterTick(new Date('2025-11-01T00:00:00').getTime()),
    ).toBe("Q4 '25")
  })
})

describe('parseDate', () => {
  it('parses a date-only string', () => {
    expect(parseDate('2025-03-31')).not.toBeNull()
  })

  it('returns null for an invalid string', () => {
    expect(parseDate('not-a-date')).toBeNull()
  })
})

describe('formatDate', () => {
  it('formats a date-only string the same in any time zone', () => {
    expect(formatDate('2025-03-31')).toBe('Mar 31, 2025')
  })

  it('falls back to the raw input when it cannot parse', () => {
    expect(formatDate('not-a-date')).toBe('not-a-date')
  })
})

describe('formatMonthDay', () => {
  it('formats a date as a short month and day, with no year', () => {
    expect(formatMonthDay('2026-01-31')).toBe('Jan 31')
    expect(formatMonthDay('2026-03-15')).toBe('Mar 15')
  })

  it('falls back to the raw input when it cannot parse', () => {
    expect(formatMonthDay('not-a-date')).toBe('not-a-date')
  })
})
