import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCompanies, getKpis } from '../api/client'
import type { CompanySummary } from '../api/types'
import { useApi } from '../hooks/useApi'
import { useDebounce } from '../hooks/useDebounce'

const DEBOUNCE_MS = 250

/**
 * The global search. It groups matches into Companies, Sectors, and KPIs.
 *
 * Companies come from GET /companies?search=, debounced so a request fires
 * once the user pauses. Sectors are derived from those same company results
 * (there is no sector entity). KPIs come from GET /kpis, fetched once and
 * filtered in the browser, since there are only five.
 *
 * Selecting a company opens its page; selecting a sector or a KPI opens the
 * overview filtered by that term, because those do not have a page of their
 * own.
 */
export default function SearchBar() {
  const navigate = useNavigate()
  const containerRef = useRef<HTMLDivElement>(null)

  const [query, setQuery] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [companies, setCompanies] = useState<CompanySummary[]>([])

  const debouncedQuery = useDebounce(query, DEBOUNCE_MS)
  const { data: kpis } = useApi(() => getKpis(), [])

  // Fetch matching companies whenever the debounced query changes. An empty
  // query fetches nothing; stale results stay in state but are never shown,
  // because the dropdown is hidden while the input is empty.
  useEffect(() => {
    const term = debouncedQuery.trim()
    if (term === '') return
    let ignore = false
    getCompanies(term)
      .then((result) => {
        if (!ignore) setCompanies(result)
      })
      .catch(() => {
        if (!ignore) setCompanies([])
      })
    return () => {
      ignore = true
    }
  }, [debouncedQuery])

  // Close the dropdown when a click lands outside the search box.
  useEffect(() => {
    function onMouseDown(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsFocused(false)
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [])

  const term = debouncedQuery.trim().toLowerCase()
  const sectorResults =
    term === ''
      ? []
      : [
          ...new Set(
            companies
              .map((company) => company.sector)
              .filter((sector) => sector.toLowerCase().includes(term)),
          ),
        ]
  const kpiResults =
    term === ''
      ? []
      : (kpis ?? []).filter((kpi) => kpi.name.toLowerCase().includes(term))

  const hasResults =
    companies.length > 0 || sectorResults.length > 0 || kpiResults.length > 0
  const isDebouncing = query.trim() !== debouncedQuery.trim()
  const showDropdown = isFocused && query.trim() !== ''

  function go(path: string) {
    setQuery('')
    setIsFocused(false)
    navigate(path)
  }

  return (
    <div className="search" ref={containerRef}>
      <input
        className="search-input"
        type="search"
        placeholder="Search company, sector, or KPI..."
        value={query}
        onFocus={() => setIsFocused(true)}
        onChange={(event) => setQuery(event.target.value)}
        aria-label="Search company, sector, or KPI"
      />
      {showDropdown && (
        <div className="search-results">
          {!hasResults ? (
            <div className="search-empty">
              {isDebouncing
                ? 'Searching...'
                : `No matches for "${query.trim()}".`}
            </div>
          ) : (
            <>
              {companies.length > 0 && (
                <div className="search-group">
                  <div className="search-group-title">Companies</div>
                  {companies.map((company) => (
                    <button
                      key={company.ticker}
                      type="button"
                      className="search-result"
                      onClick={() =>
                        go(`/companies/${encodeURIComponent(company.ticker)}`)
                      }
                    >
                      {company.name}{' '}
                      <span className="search-result-meta">
                        {company.ticker}
                      </span>
                    </button>
                  ))}
                </div>
              )}
              {sectorResults.length > 0 && (
                <div className="search-group">
                  <div className="search-group-title">Sectors</div>
                  {sectorResults.map((sector) => (
                    <button
                      key={sector}
                      type="button"
                      className="search-result"
                      onClick={() => go(`/?search=${encodeURIComponent(sector)}`)}
                    >
                      {sector}
                    </button>
                  ))}
                </div>
              )}
              {kpiResults.length > 0 && (
                <div className="search-group">
                  <div className="search-group-title">KPIs</div>
                  {kpiResults.map((kpi) => (
                    <button
                      key={kpi.name}
                      type="button"
                      className="search-result"
                      onClick={() =>
                        go(`/?search=${encodeURIComponent(kpi.name)}`)
                      }
                    >
                      {kpi.name}{' '}
                      <span className="search-result-meta">{kpi.unit}</span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
