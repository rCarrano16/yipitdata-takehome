import { useRef } from 'react'
import type { KeyboardEvent } from 'react'
import { PERIOD_PRESETS } from '../lib/periodPresets'
import type { Preset } from '../lib/periodPresets'

interface PeriodFilterProps {
  selected: Preset
  onSelect: (preset: Preset) => void
}

/**
 * A segmented control that picks the chart's time window from fiscal-period
 * presets. It replaces the free-form From/To date inputs.
 *
 * The presets are mutually exclusive, so this is an ARIA radio group: the
 * container is `role="radiogroup"`, each segment is `role="radio"`, and a
 * roving tabindex keeps the whole group a single Tab stop. Arrow keys move the
 * selection between segments; Enter or Space (native to a `<button>`) also
 * selects the focused one.
 */
export default function PeriodFilter({ selected, onSelect }: PeriodFilterProps) {
  const segmentsRef = useRef<(HTMLButtonElement | null)[]>([])

  function handleKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    let nextIndex: number
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      nextIndex = (index + 1) % PERIOD_PRESETS.length
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      nextIndex = (index - 1 + PERIOD_PRESETS.length) % PERIOD_PRESETS.length
    } else {
      return
    }
    event.preventDefault()
    onSelect(PERIOD_PRESETS[nextIndex].value)
    segmentsRef.current[nextIndex]?.focus()
  }

  return (
    <div
      className="period-filter"
      role="radiogroup"
      aria-label="Chart time period"
    >
      {PERIOD_PRESETS.map((preset, index) => (
        <button
          key={preset.value}
          ref={(element) => {
            segmentsRef.current[index] = element
          }}
          type="button"
          role="radio"
          aria-checked={selected === preset.value}
          tabIndex={selected === preset.value ? 0 : -1}
          className="period-segment"
          onClick={() => onSelect(preset.value)}
          onKeyDown={(event) => handleKeyDown(event, index)}
        >
          {preset.label}
        </button>
      ))}
    </div>
  )
}
