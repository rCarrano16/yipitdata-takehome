import { describe, expect, it } from 'vitest'
import type { SeriesDetail } from '../api/types'
import { csvFileName, seriesToCsv } from './exportCsv'

function makeSeries(): SeriesDetail {
  return {
    ticker: 'ACME',
    company_name: 'Acme Corp',
    kpi: 'ASP ($)',
    unit: '$',
    history: [
      {
        period: '2025Q4',
        period_start: '2025-10-01',
        period_end: '2025-12-31',
        value: 120.5,
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
    ],
    current_qtd: {
      period: '2026Q1',
      period_start: '2026-01-01',
      period_end: '2026-03-31',
      value: 40,
      as_of: '2026-01-31',
      created_at: '2026-02-01T00:00:00Z',
    },
    last_updated: '2026-02-01T00:00:00Z',
  }
}

describe('seriesToCsv', () => {
  it('writes a header plus one row per estimate', () => {
    const lines = seriesToCsv(makeSeries()).split('\r\n')
    expect(lines).toHaveLength(3)
    expect(lines[0]).toBe(
      'kpi,unit,estimate_type,period,period_start,period_end,value,as_of,created_at',
    )
  })

  it('tags history and QTD rows, leaving as_of empty for history', () => {
    const lines = seriesToCsv(makeSeries()).split('\r\n')
    expect(lines[1]).toBe(
      'ASP ($),$,historical,2025Q4,2025-10-01,2025-12-31,120.5,,2026-01-02T00:00:00Z',
    )
    expect(lines[2]).toBe(
      'ASP ($),$,qtd,2026Q1,2026-01-01,2026-03-31,40,2026-01-31,2026-02-01T00:00:00Z',
    )
  })

  it('quotes a field that contains a comma', () => {
    const series = makeSeries()
    series.kpi = 'Revenue, net'
    const lines = seriesToCsv(series).split('\r\n')
    expect(lines[1].startsWith('"Revenue, net"')).toBe(true)
  })
})

describe('csvFileName', () => {
  it('builds a safe, dated file name', () => {
    expect(csvFileName(makeSeries())).toMatch(
      /^ACME_ASP_\d{4}-\d{2}-\d{2}\.csv$/,
    )
  })
})
