import { Suspense } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import LoadingState from './components/LoadingState'
import SearchBar from './components/SearchBar'

// The layout shell: a sticky header with the title and the global search, and
// a <main> where the routed page renders. SearchBar stays mounted across
// navigations, so its one-time KPI fetch is not repeated. The <Suspense>
// covers the lazily loaded series page, so only the content area shows a
// fallback while its chunk loads, not the whole shell.
export default function App() {
  // Key the routed content by pathname so navigating to a different resource
  // remounts the page: it then does a clean data fetch instead of briefly
  // showing the previous resource's data. A SeriesPage date-filter change is
  // local state, not a route change, so it does not remount the page and the
  // chart stays on screen.
  const { pathname } = useLocation()
  return (
    <div className="app">
      <header className="app-header">
        <div className="container app-header-inner">
          <Link to="/" className="app-title">
            KPI Estimates Portal
          </Link>
          <SearchBar />
        </div>
      </header>
      <main className="container app-main">
        <Suspense fallback={<LoadingState />}>
          <Outlet key={pathname} />
        </Suspense>
      </main>
    </div>
  )
}
