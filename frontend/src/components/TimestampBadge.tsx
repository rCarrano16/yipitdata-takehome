import { formatDate, formatDateTime } from '../lib/format'

interface TimestampBadgeProps {
  lastUpdated: string | null
  qtdAsOf: string | null
  filtered: boolean
}

/**
 * The two timestamps the assignment asks for. They are distinct concepts:
 * `qtdAsOf` is the effective date of the current QTD snapshot (a domain
 * value), `lastUpdated` is the most recent write time across the series (the
 * audit value).
 *
 * Under a date filter the backend's `current_qtd` is the latest snapshot
 * within the range, not the true current QTD, so `filtered` switches the QTD
 * label to say so rather than mislabel an in-range snapshot as the current
 * estimate.
 */
export default function TimestampBadge({
  lastUpdated,
  qtdAsOf,
  filtered,
}: TimestampBadgeProps) {
  return (
    <div className="timestamps">
      <span className="timestamp">
        {filtered ? 'Latest QTD in range, as of' : 'QTD as of'}{' '}
        <strong>{qtdAsOf ? formatDate(qtdAsOf) : 'n/a'}</strong>
      </span>
      <span className="timestamp">
        Last updated{' '}
        <strong>{lastUpdated ? formatDateTime(lastUpdated) : 'n/a'}</strong>
      </span>
    </div>
  )
}
