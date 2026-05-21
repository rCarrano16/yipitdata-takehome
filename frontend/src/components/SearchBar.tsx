import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
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
 * own. The dropdown is keyboard navigable: ArrowDown / ArrowUp move the
 * highlight, Enter opens the highlighted result, Escape closes the dropdown.
 */
export default function SearchBar() {
  const navigate = useNavigate()
  const containerRef = useRef<HTMLDivElement>(null)

  const [query, setQuery] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [companies, setCompanies] = useState<CompanySummary[]>([])
  // The trimmed query `companies` was fetched for. Comparing it to the live
  // query tells us whether the results still match what the box shows: if they
  // do not, they are stale, and the dropdown shows "Searching..." instead of
  // the previous query's hits.
  const [resultsTerm, setResultsTerm] = useState('')
  // The highlighted result, as an index into the flattened result list, or -1
  // for no highlight. Driven by the arrow keys and by mouse hover.
  const [activeIndex, setActiveIndex] = useState(-1)

  const debouncedQuery = useDebounce(query, DEBOUNCE_MS)
  const { data: kpis } = useApi(() => getKpis(), [])

  // Fetch matching companies whenever the debounced query settles. The fetched
  // term is recorded in `resultsTerm` alongside the results, so a result from
  // an older query is never shown against a newer one.
  useEffect(() => {
    const term = debouncedQuery.trim()
    // Nothing to fetch for an empty query. Any prior results stay in state but
    // are never shown: `resultsTerm` no longer equals the query, so the
    // staleness check below keeps them out of the dropdown.
    if (term === '') return
    let ignore = false
    getCompanies(term)
      .then((result) => {
        if (!ignore) {
          setCompanies(result)
          setResultsTerm(term)
        }
      })
      .catch(() => {
        if (!ignore) {
          setCompanies([])
          setResultsTerm(term)
        }
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

  // Keep the highlighted result scrolled into view as the arrows move it.
  useEffect(() => {
    if (activeIndex < 0) return
    containerRef.current
      ?.querySelector('.search-result.is-active')
      ?.scrollIntoView({ block: 'nearest' })
  }, [activeIndex])

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

  // The visible results flattened to their navigation targets, in display
  // order (companies, then sectors, then KPIs). This is what the arrow keys
  // step through and what Enter opens.
  const flatResults = [
    ...companies.map(
      (company) => `/companies/${encodeURIComponent(company.ticker)}`,
    ),
    ...sectorResults.map((sector) => `/?search=${encodeURIComponent(sector)}`),
    ...kpiResults.map((kpi) => `/?search=${encodeURIComponent(kpi.name)}`),
  ]
  // Offsets of each group's first item within the flattened list, so a
  // rendered button can compute its own flat index for the keyboard highlight.
  const sectorOffset = companies.length
  const kpiOffset = companies.length + sectorResults.length

  // Results are fresh only when they were fetched for exactly the current
  // query; otherwise the dropdown shows a loading state, never stale hits.
  const resultsAreFresh = query.trim() !== '' && resultsTerm === query.trim()
  const hasResults = flatResults.length > 0
  const showDropdown = isFocused && query.trim() !== ''

  function go(path: string) {
    setQuery('')
    setIsFocused(false)
    setActiveIndex(-1)
    navigate(path)
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!showDropdown) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, flatResults.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, -1))
    } else if (event.key === 'Enter') {
      if (activeIndex >= 0 && activeIndex < flatResults.length) {
        event.preventDefault()
        go(flatResults[activeIndex])
      }
    } else if (event.key === 'Escape') {
      setIsFocused(false)
      setActiveIndex(-1)
    }
  }

  function resultClass(index: number): string {
    return index === activeIndex ? 'search-result is-active' : 'search-result'
  }

  return (
    <div className="search" ref={containerRef}>
      <input
        className="search-input"
        type="search"
        placeholder="Search company, sector, or KPI..."
        value={query}
        onFocus={() => setIsFocused(true)}
        onChange={(event) => {
          setQuery(event.target.value)
          setActiveIndex(-1)
        }}
        onKeyDown={onKeyDown}
        aria-label="Search company, sector, or KPI"
      />
      {showDropdown && (
        <div className="search-results">
          {!resultsAreFresh ? (
            <div className="search-empty">Searching...</div>
          ) : !hasResults ? (
            <div className="search-empty">
              No matches for "{query.trim()}".
            </div>
          ) : (
            <>
              {companies.length > 0 && (
                <div className="search-group">
                  <div className="search-group-title">Companies</div>
                  {companies.map((company, i) => (
                    <button
                      key={company.ticker}
                      type="button"
                      className={resultClass(i)}
                      onMouseEnter={() => setActiveIndex(i)}
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
                  {sectorResults.map((sector, j) => (
                    <button
                      key={sector}
                      type="button"
                      className={resultClass(sectorOffset + j)}
                      onMouseEnter={() => setActiveIndex(sectorOffset + j)}
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
                  {kpiResults.map((kpi, k) => (
                    <button
                      key={kpi.name}
                      type="button"
                      className={resultClass(kpiOffset + k)}
                      onMouseEnter={() => setActiveIndex(kpiOffset + k)}
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
