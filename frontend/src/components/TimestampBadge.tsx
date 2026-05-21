import { formatDate, formatDateTime } from '../lib/format'

interface TimestampBadgeProps {
  lastUpdated: string | null
  qtdAsOf: string | null
}

/**
 * The two timestamps the assignment asks for. They are distinct concepts:
 * `qtdAsOf` is the effective date of the current QTD snapshot (a domain
 * value), `lastUpdated` is the most recent write time across the series (the
 * audit value).
 */
export default function TimestampBadge({
  lastUpdated,
  qtdAsOf,
}: TimestampBadgeProps) {
  return (
    <div className="timestamps">
      <span className="timestamp">
        QTD as of <strong>{qtdAsOf ? formatDate(qtdAsOf) : 'n/a'}</strong>
      </span>
      <span className="timestamp">
        Last updated{' '}
        <strong>{lastUpdated ? formatDateTime(lastUpdated) : 'n/a'}</strong>
      </span>
    </div>
  )
}
