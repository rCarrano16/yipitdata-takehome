import { Link, useSearchParams } from 'react-router-dom'
import { getOverview } from '../api/client'
import type { OverviewCard } from '../api/types'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import SummaryCard from '../components/SummaryCard'
import { useApi } from '../hooks/useApi'

interface CompanyGroup {
  ticker: string
  companyName: string
  sector: string
  cards: OverviewCard[]
}

/**
 * Group the flat card list by company. The backend already sorts cards by
 * (ticker, kpi), so a Map keyed on ticker yields the companies in ticker order
 * with each company's KPIs in order. The grouping makes 100 cards scannable.
 */
function groupByCompany(cards: OverviewCard[]): CompanyGroup[] {
  const byTicker = new Map<string, CompanyGroup>()
  for (const card of cards) {
    let group = byTicker.get(card.ticker)
    if (!group) {
      group = {
        ticker: card.ticker,
        companyName: card.company_name,
        sector: card.sector,
        cards: [],
      }
      byTicker.set(card.ticker, group)
    }
    group.cards.push(card)
  }
  return [...byTicker.values()]
}

/**
 * The glance tier: one summary card per (company, KPI) series, grouped under a
 * company header. An optional `?search=` in the URL filters the cards; that is
 * also where a sector or KPI search result lands.
 */
export default function OverviewPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const search = searchParams.get('search') ?? ''

  const { data, loading, error, reload } = useApi(
    () => getOverview(search || undefined),
    [search],
  )

  if (loading && !data) {
    return <LoadingState message="Loading overview..." />
  }
  if (error && !data) {
    return <ErrorState message={error.message} onRetry={reload} />
  }
  if (!data) {
    return null
  }

  const groups = groupByCompany(data.cards)

  return (
    <div>
      <h1 className="page-title">KPI Overview</h1>
      <p className="page-subtitle">
        The latest closed quarter and the current quarter-to-date estimate for
        every tracked series.
      </p>

      {search && (
        <div className="overview-toolbar">
          <span className="filter-chip">Filtered by "{search}"</span>
          <button
            type="button"
            className="btn"
            onClick={() => setSearchParams({})}
          >
            Clear filter
          </button>
        </div>
      )}

      {groups.length === 0 ? (
        <div className="state">No series match "{search}".</div>
      ) : (
        groups.map((group) => (
          <section className="company-section" key={group.ticker}>
            <div className="company-section-header">
              <Link
                to={`/companies/${encodeURIComponent(group.ticker)}`}
                className="company-section-name"
              >
                {group.companyName}
              </Link>
              <span className="company-section-meta">
                {group.ticker} &middot; {group.sector}
              </span>
            </div>
            <div className="card-grid">
              {group.cards.map((card) => (
                <SummaryCard
                  key={card.kpi}
                  ticker={card.ticker}
                  kpi={card.kpi}
                  unit={card.unit}
                  latestValue={card.latest_historical_value}
                  latestPeriod={card.latest_historical_period}
                  qtdValue={card.current_qtd_value}
                  qtdAsOf={card.current_qtd_as_of}
                  sparkline={card.sparkline}
                />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  )
}
