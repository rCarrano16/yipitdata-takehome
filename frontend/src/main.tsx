import { lazy, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import App from './App'
import CompanyPage from './pages/CompanyPage'
import NotFoundPage from './pages/NotFoundPage'
import OverviewPage from './pages/OverviewPage'
import './styles.css'

// SeriesPage pulls in the chart library, which is the bulk of the bundle.
// Loading it on demand keeps that weight off the glance tier; App wraps the
// routed outlet in a <Suspense> that covers the load. main.tsx is the entry
// module and has no exports, so the react-refresh export rule does not apply.
// eslint-disable-next-line react-refresh/only-export-components
const SeriesPage = lazy(() => import('./pages/SeriesPage'))

// The router is mounted once here. App is the layout shell; the four routes
// render into its <Outlet/>. The :kpi segment can contain spaces and other
// characters, so every link that targets it must encodeURIComponent the value.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<OverviewPage />} />
          <Route path="companies/:ticker" element={<CompanyPage />} />
          <Route path="companies/:ticker/kpis/:kpi" element={<SeriesPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
