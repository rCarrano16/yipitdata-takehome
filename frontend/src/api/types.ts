/**
 * TypeScript mirror of the backend Pydantic schemas (backend/app/schemas.py).
 *
 * JSON has no date type, so every `date` and `datetime` field arrives as an
 * ISO string (date-only "YYYY-MM-DD" or a full datetime). lib/format.ts is the
 * single place those strings are parsed and formatted for display.
 *
 * These types are hand-maintained. They are small and live in one file;
 * generating them from the backend OpenAPI schema is noted as future work.
 */

/** A company as it appears in a list or a search result. */
export interface CompanySummary {
  ticker: string
  name: string
  sector: string
}

/** A KPI and the unit its values are measured in. */
export interface KpiInfo {
  name: string
  unit: string
}

/** One closed-quarter historical estimate: a single point on the history line. */
export interface EstimatePoint {
  period: string
  period_start: string
  period_end: string
  value: number
  created_at: string
}

/** One intra-quarter QTD snapshot, stamped with the as_of date it is effective for. */
export interface QtdSnapshot {
  period: string
  period_start: string
  period_end: string
  value: number
  as_of: string
  created_at: string
}

/** The full (company, KPI) time series: closed-quarter history plus QTD snapshots. */
export interface SeriesDetail {
  ticker: string
  company_name: string
  kpi: string
  unit: string
  history: EstimatePoint[]
  qtd_snapshots: QtdSnapshot[]
  current_qtd: QtdSnapshot | null
  last_updated: string | null
}

/** Every KPI series for one company. */
export interface CompanyEstimates {
  ticker: string
  company_name: string
  sector: string
  series: SeriesDetail[]
}
