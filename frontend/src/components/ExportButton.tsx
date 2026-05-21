import type { SeriesDetail } from '../api/types'
import { downloadSeriesCsv } from '../lib/exportCsv'

interface ExportButtonProps {
  series: SeriesDetail
  disabled?: boolean
}

/** Downloads the series currently on screen as a CSV file. */
export default function ExportButton({ series, disabled }: ExportButtonProps) {
  return (
    <button
      type="button"
      className="btn"
      disabled={disabled}
      onClick={() => downloadSeriesCsv(series)}
    >
      Export CSV
    </button>
  )
}
