import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getCompanies, getKpis } from '../api/client'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import { useApi } from '../hooks/useApi'

/**
 * The landing page: a search-first directory of every tracked company.
 *
 * The full company list (about 20) and the KPI list (5) are each fetched once
 * on mount; all filtering then happens in the browser, synchronously. There is
 * no per-keystroke request and no debounce, so there are never stale async
 * results to reconcile.
 *
 * Two URL parameters carry the shareable directory state:
 * - `?sector=` narrows the list to one sector (also driven by the sector select).
 * - `?kpi=` puts the directory in KPI-scoped mode: every row then deep-links to
 *   that company's series page for the scoped KPI instead of the company page.
 * The free-text query is transient local state and is not put in the URL.
 */
export default function DirectoryPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const sector = searchParams.get('sector') ?? ''
  const kpi = searchParams.get('kpi') ?? ''
  const [query, setQuery] = useState('')

  const companiesApi = useApi(() => getCompanies(), [])
  const kpisApi = useApi(() => getKpis(), [])

  const companies = companiesApi.data
  const kpis = kpisApi.data
  const loadError = companiesApi.error ?? kpisApi.error

  // The directory only ever does this one initial load, so a full-page error
  // is the right failure mode (no non-blocking banner is needed here).
  if (loadError && (!companies || !kpis)) {
    return (
      <ErrorState
        message={loadError.message}
        onRetry={() => {
          companiesApi.reload()
          kpisApi.reload()
        }}
      />
    )
  }
  if (!companies || !kpis) {
    return <LoadingState message="Loading directory..." />
  }

  // The distinct sectors, for the sector <select>.
  const sectors = [...new Set(companies.map((company) => company.sector))].sort()

  // One matching rule for the free-text query: a case-insensitive substring
  // over the company name, ticker, and sector. The sector select narrows it
  // further.
  const q = query.trim().toLowerCase()
  const filtered = companies.filter((company) => {
    if (sector && company.sector !== sector) return false
    if (q === '') return true
    return (
      company.name.toLowerCase().includes(q) ||
      company.ticker.toLowerCase().includes(q) ||
      company.sector.toLowerCase().includes(q)
    )
  })

  // A KPI term cannot narrow a company list (every company reports all five
  // KPIs), so a query that matches KPI names surfaces an inline scope action
  // for each match instead, using the same substring rule.
  const matchedKpis =
    q === '' ? [] : kpis.filter((item) => item.name.toLowerCase().includes(q))

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next)
  }

  function scopeToKpi(name: string) {
    // The query matched a KPI, not a company, so clearing it lets the full
    // (now KPI-scoped) company list show.
    setQuery('')
    updateParam('kpi', name)
  }

  function rowTarget(ticker: string): string {
    const encoded = encodeURIComponent(ticker)
    return kpi
      ? `/companies/${encoded}/kpis/${encodeURIComponent(kpi)}`
      : `/companies/${encoded}`
  }

  // The count line doubles as the aria-live region: it announces the result
  // count and whether any KPI suggestions are present.
  const countParts = [
    `${filtered.length} ${filtered.length === 1 ? 'company' : 'companies'}`,
  ]
  if (matchedKpis.length > 0) {
    const noun = matchedKpis.length === 1 ? 'suggestion' : 'suggestions'
    countParts.push(`${matchedKpis.length} KPI ${noun}`)
  }
  const countText = countParts.join(', ')

  return (
    <div>
      <h1 className="page-title">Company Directory</h1>
      <p className="page-subtitle">
        Search the tracked companies, or scope to a KPI to jump straight to a
        series.
      </p>

      <div className="directory-controls">
        <div className="directory-field directory-field-grow">
          <label htmlFor="directory-search">Search</label>
          <input
            id="directory-search"
            className="directory-search"
            type="search"
            placeholder="Search by company, ticker, or sector..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <div className="directory-field">
          <label htmlFor="directory-sector">Sector</label>
          <select
            id="directory-sector"
            className="directory-sector"
            value={sector}
            onChange={(event) => updateParam('sector', event.target.value)}
          >
            <option value="">All sectors</option>
            {sectors.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {(sector || kpi) && (
        <div className="directory-chips">
          {sector && (
            <span className="filter-chip">
              Sector: {sector}
              <button
                type="button"
                className="filter-chip-clear"
                aria-label={`Clear the ${sector} sector filter`}
                onClick={() => updateParam('sector', '')}
              >
                &times;
              </button>
            </span>
          )}
          {kpi && (
            <span className="filter-chip">
              KPI: {kpi}
              <button
                type="button"
                className="filter-chip-clear"
                aria-label={`Clear the ${kpi} KPI scope`}
                onClick={() => updateParam('kpi', '')}
              >
                &times;
              </button>
            </span>
          )}
        </div>
      )}

      {matchedKpis.length > 0 && (
        <div className="directory-suggestions">
          {matchedKpis.map((item) => (
            <button
              key={item.name}
              type="button"
              className="directory-suggestion"
              onClick={() => scopeToKpi(item.name)}
            >
              Scope to KPI: {item.name}
            </button>
          ))}
        </div>
      )}

      <p className="directory-count" aria-live="polite">
        {countText}
      </p>

      {filtered.length > 0 ? (
        <ul className="directory-list">
          {filtered.map((company) => (
            <li key={company.ticker}>
              <Link className="directory-row" to={rowTarget(company.ticker)}>
                <span className="directory-row-name">{company.name}</span>
                <span className="directory-row-ticker">{company.ticker}</span>
                <span className="directory-row-sector">{company.sector}</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : matchedKpis.length === 0 ? (
        <div className="state">
          {q
            ? `No companies match "${query.trim()}".`
            : 'No companies to show.'}
        </div>
      ) : null}
    </div>
  )
}
