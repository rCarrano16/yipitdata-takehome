import { describe, expect, it } from 'vitest'
import type { SeriesDetail } from '../api/types'
import { toHistorySeries, toQtdSeries } from './chartData'

function makeSeries(): SeriesDetail {
  return {
    ticker: 'ACME',
    company_name: 'Acme Corp',
    kpi: 'Total Revenue ($MM)',
    unit: '$MM',
    history: [
      {
        period: '2025Q3',
        period_start: '2025-07-01',
        period_end: '2025-09-30',
        value: 100,
        created_at: '2025-10-01T00:00:00Z',
      },
      {
        period: '2025Q4',
        period_start: '2025-10-01',
        period_end: '2025-12-31',
        value: 120,
        created_at: '2026-01-02T00:00:00Z',
      },
    ],
    qtd_snapshots: [
      {
        period: '2026Q1',
        period_start: '2026-01-01',
        period_end: '2026-03-31',
        value: 40,
        as_of: '2026-01-31',
        created_at: '2026-02-01T00:00:00Z',
      },
      {
        period: '2026Q1',
        period_start: '2026-01-01',
        period_end: '2026-03-31',
        value: 55,
        as_of: '2026-02-28',
        created_at: '2026-03-01T00:00:00Z',
      },
    ],
    current_qtd: {
      period: '2026Q1',
      period_start: '2026-01-01',
      period_end: '2026-03-31',
      value: 55,
      as_of: '2026-02-28',
      created_at: '2026-03-01T00:00:00Z',
    },
    last_updated: '2026-03-01T00:00:00Z',
    analytics: { latest_period: '2025Q4', qoq: 0.2, yoy: null },
  }
}

describe('toHistorySeries', () => {
  it('maps each closed quarter to a time-stamped point', () => {
    const points = toHistorySeries(makeSeries())
    expect(points).toHaveLength(2)
    expect(points[0]).toEqual({
      t: new Date('2025-09-30T00:00:00').getTime(),
      value: 100,
      period: '2025Q3',
    })
  })

  it('sorts out-of-order history by time', () => {
    const series = makeSeries()
    series.history.reverse()
    const points = toHistorySeries(series)
    expect(points.map((point) => point.period)).toEqual(['2025Q3', '2025Q4'])
  })

  it('excludes the QTD snapshots', () => {
    const points = toHistorySeries(makeSeries())
    expect(points).toHaveLength(2)
    expect(points.some((point) => point.period === '2026Q1')).toBe(false)
  })

  it('returns an empty array when there is no history', () => {
    const series = makeSeries()
    series.history = []
    expect(toHistorySeries(series)).toEqual([])
  })
})

describe('toQtdSeries', () => {
  it('maps each snapshot to an as_of-stamped point', () => {
    const points = toQtdSeries(makeSeries())
    expect(points).toHaveLength(2)
    expect(points[0]).toEqual({
      asOf: '2026-01-31',
      value: 40,
      period: '2026Q1',
    })
  })

  it('sorts out-of-order snapshots by as_of', () => {
    const series = makeSeries()
    series.qtd_snapshots.reverse()
    const points = toQtdSeries(series)
    expect(points.map((point) => point.asOf)).toEqual([
      '2026-01-31',
      '2026-02-28',
    ])
  })

  it('excludes the closed-quarter history', () => {
    const points = toQtdSeries(makeSeries())
    expect(points).toHaveLength(2)
    expect(points.some((point) => point.period.startsWith('2025'))).toBe(false)
  })

  it('returns an empty array when there are no snapshots', () => {
    const series = makeSeries()
    series.qtd_snapshots = []
    expect(toQtdSeries(series)).toEqual([])
  })
})
