import { Suspense } from 'react'
import { Link, Outlet } from 'react-router-dom'
import LoadingState from './components/LoadingState'
import SearchBar from './components/SearchBar'

// The layout shell: a sticky header with the title and the global search, and
// a <main> where the routed page renders. SearchBar stays mounted across
// navigations, so its one-time KPI fetch is not repeated. The <Suspense>
// covers the lazily loaded series page, so only the content area shows a
// fallback while its chunk loads, not the whole shell.
export default function App() {
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
          <Outlet />
        </Suspense>
      </main>
    </div>
  )
}
