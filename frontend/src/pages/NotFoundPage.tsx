import { Link } from 'react-router-dom'

/** The fallback for any unmatched route. */
export default function NotFoundPage() {
  return (
    <div className="notfound">
      <h1>404</h1>
      <p className="muted">This page does not exist.</p>
      <p>
        <Link to="/">Back to the directory</Link>
      </p>
    </div>
  )
}
