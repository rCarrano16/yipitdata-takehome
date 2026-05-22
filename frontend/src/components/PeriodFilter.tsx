import { useRef } from 'react'
import type { KeyboardEvent } from 'react'
import { FILTER_MODES } from '../lib/periodPresets'
import type { FilterMode } from '../lib/periodPresets'
import {
  AVAILABLE_QUARTERS,
  compareQuarters,
  parseQuarter,
  quarterLabel,
} from '../lib/quarters'
import type { Quarter, QuarterRange } from '../lib/quarters'

interface PeriodFilterProps {
  selected: FilterMode
  onSelect: (mode: FilterMode) => void
  customRange: QuarterRange
  onCustomRangeChange: (range: QuarterRange) => void
}

interface QuarterSelectProps {
  id: string
  label: string
  value: Quarter
  onChange: (quarter: Quarter) => void
}

/** One labelled dropdown listing every dataset quarter. Used for both bounds. */
function QuarterSelect({ id, label, value, onChange }: QuarterSelectProps) {
  return (
    <div className="period-custom-field">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        className="period-custom-select"
        value={quarterLabel(value)}
        onChange={(event) => onChange(parseQuarter(event.target.value))}
      >
        {AVAILABLE_QUARTERS.map((quarter) => {
          const optionLabel = quarterLabel(quarter)
          return (
            <option key={optionLabel} value={optionLabel}>
              {optionLabel}
            </option>
          )
        })}
      </select>
    </div>
  )
}

/**
 * A segmented control that picks the chart's time window. Four entries are
 * fixed presets; the fifth, "Custom", reveals two quarter dropdowns for an
 * explicit start-to-end range.
 *
 * The segments are mutually exclusive, so the control is an ARIA radio group:
 * the container is `role="radiogroup"`, each segment is `role="radio"`, and a
 * roving tabindex keeps the whole group a single Tab stop. Arrow keys move the
 * selection between segments; Enter or Space (native to a `<button>`) also
 * selects the focused one.
 *
 * The two custom dropdowns stay ordered: moving one bound past the other snaps
 * the other bound to match, so the range is never inverted and no caller has to
 * defend against from > to.
 */
export default function PeriodFilter({
  selected,
  onSelect,
  customRange,
  onCustomRangeChange,
}: PeriodFilterProps) {
  const segmentsRef = useRef<(HTMLButtonElement | null)[]>([])

  function handleKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    let nextIndex: number
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      nextIndex = (index + 1) % FILTER_MODES.length
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      nextIndex = (index - 1 + FILTER_MODES.length) % FILTER_MODES.length
    } else {
      return
    }
    event.preventDefault()
    onSelect(FILTER_MODES[nextIndex].value)
    segmentsRef.current[nextIndex]?.focus()
  }

  function handleFromChange(from: Quarter) {
    // Snap the end bound up if the new start passed it, keeping from <= to.
    const to = compareQuarters(from, customRange.to) > 0 ? from : customRange.to
    onCustomRangeChange({ from, to })
  }

  function handleToChange(to: Quarter) {
    // Snap the start bound down if the new end fell before it.
    const from =
      compareQuarters(to, customRange.from) < 0 ? to : customRange.from
    onCustomRangeChange({ from, to })
  }

  return (
    <div className="period-filter-group">
      <div
        className="period-filter"
        role="radiogroup"
        aria-label="Chart time period"
      >
        {FILTER_MODES.map((mode, index) => (
          <button
            key={mode.value}
            ref={(element) => {
              segmentsRef.current[index] = element
            }}
            type="button"
            role="radio"
            aria-checked={selected === mode.value}
            tabIndex={selected === mode.value ? 0 : -1}
            className="period-segment"
            onClick={() => onSelect(mode.value)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            {mode.label}
          </button>
        ))}
      </div>

      {selected === 'custom' && (
        <div className="period-custom">
          <QuarterSelect
            id="period-from"
            label="From quarter"
            value={customRange.from}
            onChange={handleFromChange}
          />
          <QuarterSelect
            id="period-to"
            label="To quarter"
            value={customRange.to}
            onChange={handleToChange}
          />
        </div>
      )}
    </div>
  )
}
