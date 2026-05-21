import { describe, expect, it } from 'vitest'
import type { SeriesDetail } from '../api/types'
import { toChartData } from './chartData'

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
  }
}

describe('toChartData', () => {
  it('merges history and QTD snapshots into one time-sorted array', () => {
    const points = toChartData(makeSeries())
    expect(points).toHaveLength(4)
    const times = points.map((point) => point.t)
    expect(times).toEqual([...times].sort((a, b) => a - b))
  })

  it('puts each row on exactly one of the two series', () => {
    const points = toChartData(makeSeries())
    expect(points[0].historical).toBe(100)
    expect(points[0].qtd).toBeNull()
    expect(points[3].qtd).toBe(55)
    expect(points[3].historical).toBeNull()
  })

  it('carries the as_of date on QTD rows only', () => {
    const points = toChartData(makeSeries())
    expect(points[0].asOf).toBeNull()
    expect(points[2].asOf).toBe('2026-01-31')
  })

  it('sorts out-of-order input by time', () => {
    const series = makeSeries()
    series.history.reverse()
    series.qtd_snapshots.reverse()
    const points = toChartData(series)
    expect(points.map((point) => point.period)).toEqual([
      '2025Q3',
      '2025Q4',
      '2026Q1',
      '2026Q1',
    ])
  })

  it('returns an empty array for a series with no points', () => {
    const series = makeSeries()
    series.history = []
    series.qtd_snapshots = []
    expect(toChartData(series)).toEqual([])
  })
})
