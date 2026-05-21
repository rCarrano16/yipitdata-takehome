/**
 * CSV export of a series. `seriesToCsv` and `csvFileName` are pure (and unit
 * tested); `downloadSeriesCsv` adds the browser download.
 *
 * The exported rows are exactly the series the page currently holds, so when a
 * date filter is applied the file is the filtered view, which is what "export
 * the current view" means.
 */

import type { SeriesDetail } from '../api/types'

const COLUMNS = [
  'kpi',
  'unit',
  'estimate_type',
  'period',
  'period_start',
  'period_end',
  'value',
  'as_of',
  'created_at',
] as const

/**
 * Escape a field for a CSV cell.
 *
 * First, a field that begins with =, +, -, @, a tab, or a carriage return is
 * prefixed with a single quote. A spreadsheet (Excel, Sheets, LibreOffice)
 * treats a cell starting with those characters as a formula on open; the
 * prefix neutralizes that. This is defense in depth: `period` reaches the CSV
 * from the publish endpoint, so an exported field is not guaranteed safe.
 *
 * Then RFC 4180 quoting: wrap the field in double quotes when it contains a
 * comma, a quote, or a line break, and double any embedded quote.
 */
function escapeCsvField(value: string): string {
  let field = value
  if (/^[=+\-@\t\r]/.test(field)) {
    field = `'${field}`
  }
  if (/[",\r\n]/.test(field)) {
    return `"${field.replace(/"/g, '""')}"`
  }
  return field
}

function toRow(cells: (string | number)[]): string {
  return cells.map((cell) => escapeCsvField(String(cell))).join(',')
}

/** Serialize a series (history then QTD snapshots) into RFC 4180 CSV text. */
export function seriesToCsv(series: SeriesDetail): string {
  const rows: string[] = [COLUMNS.join(',')]

  for (const point of series.history) {
    rows.push(
      toRow([
        series.kpi,
        series.unit,
        'historical',
        point.period,
        point.period_start,
        point.period_end,
        point.value,
        '',
        point.created_at,
      ]),
    )
  }

  for (const snapshot of series.qtd_snapshots) {
    rows.push(
      toRow([
        series.kpi,
        series.unit,
        'qtd',
        snapshot.period,
        snapshot.period_start,
        snapshot.period_end,
        snapshot.value,
        snapshot.as_of,
        snapshot.created_at,
      ]),
    )
  }

  return rows.join('\r\n')
}

/** A safe, descriptive file name, e.g. "ACME_ASP_2026-05-21.csv". */
export function csvFileName(series: SeriesDetail): string {
  const safeKpi = series.kpi
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  const today = new Date().toISOString().slice(0, 10)
  return `${series.ticker}_${safeKpi}_${today}.csv`
}

/** Serialize the series and trigger a browser download of the CSV file. */
export function downloadSeriesCsv(series: SeriesDetail): void {
  const blob = new Blob([seriesToCsv(series)], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = csvFileName(series)
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
