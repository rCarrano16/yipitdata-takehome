interface DateRangeFilterProps {
  from: string
  to: string
  onFromChange: (value: string) => void
  onToChange: (value: string) => void
}

/**
 * Two date inputs that bound the series view. The values are ISO date strings
 * ("YYYY-MM-DD") or empty. `min` and `max` cross-link the inputs so the range
 * cannot be inverted. The series page re-fetches when either value changes, so
 * the backend applies the filter and the chart and export stay consistent.
 */
export default function DateRangeFilter({
  from,
  to,
  onFromChange,
  onToChange,
}: DateRangeFilterProps) {
  return (
    <div className="date-filter">
      <div className="date-field">
        <label htmlFor="date-from">From</label>
        <input
          id="date-from"
          type="date"
          value={from}
          max={to || undefined}
          onChange={(event) => onFromChange(event.target.value)}
        />
      </div>
      <div className="date-field">
        <label htmlFor="date-to">To</label>
        <input
          id="date-to"
          type="date"
          value={to}
          min={from || undefined}
          onChange={(event) => onToChange(event.target.value)}
        />
      </div>
      {(from || to) && (
        <button
          type="button"
          className="btn"
          onClick={() => {
            onFromChange('')
            onToChange('')
          }}
        >
          Reset
        </button>
      )}
    </div>
  )
}
