/**
 * The typed API client. Every backend call goes through here, so the base URL,
 * JSON parsing, and error normalization live in exactly one place. No
 * component calls `fetch` directly.
 */

import type {
  CompanyEstimates,
  CompanySummary,
  KpiInfo,
  OverviewResponse,
  SeriesDetail,
} from './types'

// Vite exposes only VITE_-prefixed variables to client code. The trailing
// slash is stripped so a path with a single leading slash joins cleanly.
const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '')

/** An API call that failed: a non-2xx response, or an unreachable backend. */
export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function readDetail(res: Response): Promise<string | null> {
  // Every backend error response is JSON shaped as {"detail": ...}. A 422
  // carries an array there, so only a string detail is used as the message.
  try {
    const body: unknown = await res.json()
    if (
      body !== null &&
      typeof body === 'object' &&
      'detail' in body &&
      typeof body.detail === 'string'
    ) {
      return body.detail
    }
  } catch {
    // The body was not JSON; fall through to the generic message.
  }
  return null
}

async function request<T>(path: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`)
  } catch {
    // fetch rejects on a network failure, a refused connection, or a CORS
    // block. None of those carry a message worth showing, so normalize them.
    throw new ApiError('Could not reach the API. Is the backend running?', 0)
  }
  if (!res.ok) {
    const detail = await readDetail(res)
    throw new ApiError(
      detail ?? `Request failed with status ${res.status}.`,
      res.status,
    )
  }
  return (await res.json()) as T
}

function searchSuffix(search: string | undefined): string {
  return search ? `?search=${encodeURIComponent(search)}` : ''
}

/** The glance tier: one card per (company, KPI) series, optionally filtered. */
export function getOverview(search?: string): Promise<OverviewResponse> {
  return request<OverviewResponse>(`/overview${searchSuffix(search)}`)
}

/** Companies, optionally narrowed by a ticker / name / sector search. */
export function getCompanies(search?: string): Promise<CompanySummary[]> {
  return request<CompanySummary[]>(`/companies${searchSuffix(search)}`)
}

/** Every KPI name and its unit. */
export function getKpis(): Promise<KpiInfo[]> {
  return request<KpiInfo[]>('/kpis')
}

/** Every KPI series for one company. 404s if the ticker is unknown. */
export function getCompanyEstimates(ticker: string): Promise<CompanyEstimates> {
  return request<CompanyEstimates>(
    `/companies/${encodeURIComponent(ticker)}/estimates`,
  )
}

/**
 * One (company, KPI) series: history, QTD snapshots, current QTD. The optional
 * date bounds are inclusive and filter server-side, so the response is already
 * the filtered view that the chart and the CSV export render.
 */
export function getSeries(
  ticker: string,
  kpi: string,
  dateFrom?: string,
  dateTo?: string,
): Promise<SeriesDetail> {
  const params = new URLSearchParams()
  if (dateFrom) params.set('from', dateFrom)
  if (dateTo) params.set('to', dateTo)
  const query = params.toString()
  // encodeURIComponent is required: KPI names contain spaces and parentheses.
  const path = `/companies/${encodeURIComponent(ticker)}/kpis/${encodeURIComponent(kpi)}`
  return request<SeriesDetail>(query ? `${path}?${query}` : path)
}
