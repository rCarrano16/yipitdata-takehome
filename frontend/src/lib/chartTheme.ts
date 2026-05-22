/**
 * Design tokens the detail charts need as literal values.
 *
 * Recharts takes colors and tick styling as plain props, and `var()` does not
 * resolve inside SVG presentation attributes, so the relevant `styles.css`
 * tokens are mirrored here. This is the single source of truth for both chart
 * panels; keep these values in sync with the tokens in `styles.css`.
 */

/** `--series-history`: the closed-quarter history line. */
export const SERIES_HISTORY = '#197f9f'

/** `--series-qtd`: the quarter-to-date snapshot line. */
export const SERIES_QTD = '#f48c5c'

/** `--rule`: chart grid lines, axis lines, and tick marks. */
export const CHART_RULE = '#dde5e7'

/** `--ink`: the direct value label on a chart point. */
export const LABEL_INK = '#16242a'

/** `--ink-muted`: axis tick label text. */
const AXIS_TEXT = '#616767'

/** Axis tick label style: Roboto Mono, 11px, `--ink-muted` (design-system 8). */
export const AXIS_TICK = {
  fontSize: 11,
  fontFamily: '"Roboto Mono", monospace',
  fill: AXIS_TEXT,
}
