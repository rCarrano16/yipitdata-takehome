# Design System

The single source of truth for the portal's visual identity: color, typography,
spacing, shape, component styling, and data-visualization rules. Every page and
every component must conform to this document.

The system is grounded in YipitData's published design system
(design.yipitdata.com). Where YipitData publishes a value, this document uses it
verbatim and cites it. Where YipitData has not yet published guidance (its UI
color system is marked "Coming Soon"), values are derived in keeping with the
published palette and explicitly marked as derived.

---

## 1. Design principles

The product is a KPI estimates portal for time-constrained institutional
investors. The target aesthetic is an institutional research terminal (a "data
desk"), not a consumer SaaS app.

1. **Numbers are the product.** Numeric values get a monospaced, tabular
   treatment and the strongest position in every visual hierarchy.
2. **Separate with hairline rules, not shadows.** YipitData's dashboard guidance
   is explicit: keep backgrounds consistent and do not box content in cards.
3. **Restraint over decoration.** No gradients, no glassmorphism, no layered
   shadows. When in doubt, subtract.
4. **Color is punctuation.** The accent marks state and data series; it never
   decorates.
5. **Minimize cognitive load.** One purpose per page; the minimum content needed
   to answer the user's question.

---

## 2. Source palette

YipitData separates two palettes:

- **Brand colors** are reserved for marketing and brand expression. YipitData
  states they must not be used as the product UI design system.
- **The Charts & Visualizations palette** is the product-facing data color
  language.

Because YipitData's UI color system is not yet published, the product UI tokens
in this document are built from the **Charts & Visualizations palette**. Brand
colors are used only for the application chrome (the header), which is brand
expression rather than a product token.

### YipitData brand colors (reference)

| Name | Hex | Use in this product |
|---|---|---|
| Brand Blue | `#0D4753` | Header chrome; interactive text |
| Dark Grey | `#616767` | Muted text |
| Light Blue | `#ABD0D9` | Muted text on the dark chrome |
| Accent | `#F48D5C` | Not used directly; the chart-palette Orange is used instead |

### YipitData chart palette (product source)

Core colors, in published order (the order itself guarantees differentiation):

`#197F9F` Blue, `#5FB7AF` Teal, `#F48C5C` Orange, `#4CAF50` Green,
`#8E77FF` Purple, `#F7BB49` Yellow, `#75BFF2` Light Blue, `#ED5C6D` Red,
`#84E1D9` Cyan, `#CA75DF` Pink.

Sequential blue scale: `#D1E5EC` 100, `#A3CCD9` 300, `#8CBFCF` 400,
`#5EA5BC` 600, `#4799B2` 700, `#197F9F` 900.

---

## 3. Color tokens

These are the only colors permitted in the product. Define them as CSS custom
properties in `:root` in `frontend/src/styles.css`. Do not introduce any color
outside this table.

### Chrome (application header)

| Token | Value | Source | Usage |
|---|---|---|---|
| `--chrome` | `#0D4753` | YipitData Brand Blue | Header background |
| `--chrome-ink` | `#FFFFFF` | - | Wordmark and primary text on chrome |
| `--chrome-ink-muted` | `#ABD0D9` | YipitData Light Blue | Secondary text on chrome |
| `--chrome-rule` | `rgba(255,255,255,0.14)` | Derived | Dividers inside the chrome |

### Surfaces and neutrals

| Token | Value | Source | Usage |
|---|---|---|---|
| `--canvas` | `#F2F5F6` | Derived | Page background |
| `--surface` | `#FFFFFF` | - | Cards, panels, inputs, dropdowns |
| `--surface-sunken` | `#ECEFF1` | Derived | Subtle wash: row hover, inert fills |
| `--rule` | `#DDE5E7` | Derived | Hairline borders and dividers |
| `--ink` | `#16242A` | Derived | Primary text |
| `--ink-muted` | `#616767` | YipitData Dark Grey | Secondary text, labels |
| `--ink-subtle` | `#9AA3A5` | Derived | Placeholder text and disabled controls only; ~2.6:1 on white, never content text |

### Interactive and accent

| Token | Value | Source | Usage |
|---|---|---|---|
| `--link` | `#0D4753` | YipitData Brand Blue | Interactive text (passes AA on light) |
| `--accent` | `#197F9F` | Chart Blue 900 | Active state, focus ring, fills, hover borders |
| `--accent-hover` | `#0D4753` | Chart / Brand | Hover and pressed state on accent fills |
| `--accent-soft` | `#D1E5EC` | Chart Blue 100 | Selected-row tint, chip background |
| `--accent-soft-hover` | `#A3CCD9` | Chart Blue 300 | Hover on soft-tinted elements |

### Data series

| Token | Value | Source | Usage |
|---|---|---|---|
| `--series-history` | `#197F9F` | Chart Blue | Historical estimate line and points |
| `--series-qtd` | `#F48C5C` | Chart Orange | QTD snapshot line and points |

### Semantic

| Token | Value | Source | Usage |
|---|---|---|---|
| `--positive` | `#4CAF50` | Chart Green | Positive status only |
| `--negative` | `#ED5C6D` | Chart Red | Errors, destructive status |
| `--warning` | `#F7BB49` | Chart Yellow | Caution status |
| `--positive-soft` | `#E6F4E7` | Derived, `--positive` 14% on `--surface` | Background tint of a positive status pill |
| `--negative-soft` | `#FCE8EB` | Derived, `--negative` 14% on `--surface` | Background tint of a negative status pill |

### Elevation

| Token | Value | Source | Usage |
|---|---|---|---|
| `--shadow-overlay` | `0 8px 24px rgba(13,71,83,0.12)` | Derived, brand-tinted | Floating layers only (chart tooltip, menus) |

### Usage rules

- Surfaces never cast a shadow. The only shadow in the product is
  `--shadow-overlay`, used exclusively for floating layers.
- One accent hue. Do not bring a second interactive color into the interface.
- Semantic colors are used sparingly and only for status, never for decoration.
- The previous build used the Tailwind default palette (`#2563EB`, `#6B7280`,
  `#D97706`, `#DC2626`, `#F5F6F8`). Every one of those must be replaced by a
  token above.

---

## 4. Typography

Both families are YipitData's published typeface (Roboto), licensed under the
Open Font License and available on Google Fonts. Load `Roboto` and `Roboto Mono`
together; do not use a system-font fallback as the primary face.

- **Roboto** - all UI text.
- **Roboto Mono** - all numeric values, tickers, and chart axis labels. The
  monospaced figures give the data-desk character precisely where it matters.

### Type scale

| Role | Family | Size | Weight | Line height | Notes |
|---|---|---|---|---|---|
| Page title | Roboto | 24px | 500 | 1.25 | One per page |
| Section heading | Roboto | 16px | 500 | 1.3 | |
| Body | Roboto | 14px | 400 | 1.5 | Base size |
| Body small | Roboto | 13px | 400 | 1.5 | |
| Label / caption | Roboto | 11px | 500 | 1.4 | Uppercase, letter-spacing 0.06em, `--ink-muted` |
| KPI hero value | Roboto Mono | 30px | 500 | 1.1 | The primary number on a card |
| Data value | Roboto Mono | 14-16px | 500 | 1.2 | Tickers, QTD value, inline figures |
| Axis / tick | Roboto Mono | 11-12px | 400 | 1.0 | Chart axes |

### Rules

- Weights: Roboto 400 and 500; 700 is reserved for rare, genuine emphasis.
  Roboto Mono 400 and 500. Premium hierarchy is built with 500, not 700.
- Any number rendered in Roboto (not Roboto Mono) must set
  `font-variant-numeric: tabular-nums` so numeric columns align.
- Tickers and the KPI hero value always use Roboto Mono.
- Do not introduce sizes or weights outside this scale.

---

## 5. Spacing and layout

- Base unit: **4px**. The spacing scale is `4, 8, 12, 16, 24, 32, 48`. Do not
  use off-scale values.
- Page container: max-width `1180px`, horizontal gutter `20px`.
- Favor whitespace over borders for grouping; use a hairline rule only where a
  real separation is needed.

---

## 6. Shape and elevation

- **Radius:** `--radius: 6px` for cards, inputs, buttons, and dropdowns.
  `--radius-pill: 999px` for badges and chips. No other radii.
- **Borders:** `1px solid var(--rule)`. The hairline rule is the primary
  separation device.
- **Elevation:** surfaces are flat. Separation comes from the rule plus the
  `--canvas` / `--surface` tone difference. The single allowed shadow is
  `--shadow-overlay`, for floating layers only.
- **Focus:** every interactive element shows a visible focus state -
  `2px solid var(--accent)` outline with `2px` offset (use `-1px` inset for text
  inputs). Focus visibility is never removed.

---

## 7. Components

### Application header (chrome)

Full-width sticky bar, `60px` tall, background `--chrome`. Holds the wordmark
only ("KPI Estimates Portal", `--chrome-ink`, Roboto 500, 17px), left-aligned.
The header is calm chrome - it carries no search and no controls. The
dark-on-light contrast separates it from the canvas; an explicit bottom border
is optional.

### Directory search

The portal has one search, and it lives at the top of the company directory (the
`/` page), not in the header. There is no floating results dropdown.

- Input: background `--surface`, `1px solid var(--rule)`, `--radius`, Roboto
  14px, placeholder `--ink-subtle`. Focus shows the `--accent` outline. It spans
  the directory's content column, or close to it.
- As the user types, the company list narrows in place by company name, ticker,
  and sector, under one consistent matching rule. The list below the input is
  the result of the query.
- KPI scope: a KPI term cannot narrow a company list, because every company
  reports all five KPIs. When the query matches one or more of the five KPI
  names (a term like "Net Added Subscribers" matches two), an inline suggestion
  appears for each, between the input and the list - "Scope to KPI: {name}".
  Selecting one puts the directory in KPI-scoped mode (below). This is the only
  way a KPI term resolves; it is not a floating grouped dropdown. When a query
  matches only KPIs, the suggestions are the primary result, not an empty state.
- An empty query shows the full directory. A query that matches nothing (no
  company, sector, or KPI) shows the empty state.

### Directory KPI scope

Selecting a KPI from search scopes the directory to that KPI through a `?kpi=`
URL parameter. While the scope is active:

- A scope chip "KPI: {name}" with a clear control sits with the directory
  filters, using the filter-chip style (Filter chip, below).
- The company list is unchanged - all companies, name/ticker/sector only, no KPI
  values. The directory never renders a metric column; a column of one KPI
  across every company is a cross-company comparison view, which is out of
  scope.
- Each company row deep-links to that company's series page for the scoped KPI
  (`/companies/{ticker}/kpis/{kpi}`) rather than the company page.
- The in-place text filter still narrows by company or sector while the KPI
  scope holds.

### Company directory (the `/` page)

A vertical list of company rows. Each row carries the company name (Roboto
14px/500, `--ink`), ticker (Roboto Mono 13px, `--ink-muted`), and sector (Roboto
13px, `--ink-muted`). Rows are separated by `1px` `--rule` bottom borders, never
by shadow. Row hover: `--surface-sunken` background. Selected or active row:
`2px` `--accent` left border plus an `--accent-soft` background. Page-level
filters (search field, optional sector filter) sit on top of the list.

### KPI summary card (company page)

Not a shadowed box. A region on `--surface` bordered by `1px solid var(--rule)`,
`--radius`, no shadow. Top to bottom: KPI name (label/caption style), latest
closed value (KPI hero value style, Roboto Mono 30px, `--ink`), period caption
(`--ink-muted`), sparkline, a hairline `--rule` divider, then the QTD row -
"Current QTD" label (`--ink-muted`) with its value (Roboto Mono, `--series-qtd`)
and the as-of badge. The whole card is a link; hover sets the border to
`--accent`.

### Sparkline

Inline SVG, stroke `--series-history`, ~1.5px non-scaling stroke, no fill,
height ~32px. A trend cue only; never a substitute for the detail chart.

### Badge

Pill (`--radius-pill`), Roboto 11px/500, `--ink-muted` text, `--canvas`
background, `1px solid var(--rule)`, padding `1px 8px`.

### Trend badge

A status pill for one closed-quarter trend signal (QoQ or YoY): the label in
`--ink-muted`, the signed percent in Roboto Mono `--ink`. The tone is a soft
semantic tint, `--positive-soft` for a rise or `--negative-soft` for a fall;
the `+` / `-` sign carries the direction as text, so meaning never depends on
color alone. A null signal (no comparable quarter) uses the neutral Badge
treatment. Same pill on the summary cards and the series-page trend row.

### Filter chip

Pill, `--accent-soft` background, `--link` text, Roboto 13px/500. If removable,
the clear affordance is part of the chip.

### Buttons

- Secondary (default): `--surface` background, `1px solid var(--rule)`, `--ink`
  text, Roboto 13px/500, `--radius`. Hover: border `--accent`, text `--link`.
- Primary: `--accent` background, white text. Hover: `--accent-hover`. Use
  sparingly - the app is mostly navigation.
- Disabled: 50% opacity, no hover response.

### Inputs

`--surface` background, `1px solid var(--rule)`, `--radius`, Roboto 14px,
padding `6-8px`. Focus shows the `--accent` outline. The label sits above the
field in the label/caption style.

### States (loading, empty, error)

A centered block with generous vertical padding (~56px), `--ink-muted` text.
Error text uses `--negative`. Provide a secondary retry button where a retry is
possible. Copy is plain and specific, never generic.

### Not Found

Large numeral in Roboto Mono, a plain one-line message, and a link back to the
directory.

---

## 8. Data visualization

The detail chart and the sparkline follow YipitData's published chart
guidelines.

- **Series colors:** historical = `--series-history` (`#197F9F`), QTD =
  `--series-qtd` (`#F48C5C`). The detail view splits history and QTD into two
  separate single-series panels, so each panel carries one color; the panel
  title identifies the series and color is never the only cue.
- **Line treatment:** a clean line with a subtle area fill beneath it (a soft
  vertical fade of the series color). No dot on every point; an emphasized dot
  marks only the latest point, and a hover dot appears on interaction. Drop the
  axis lines, keep the tick labels; the hover cursor is a `--rule` hairline.
- **Legend:** only a chart with several series on one axis needs a legend
  (place it at the bottom). The two-panel detail view has one series per panel
  and uses no legend; the panel title names the series.
- **Y axis:** a panel showing an accumulating quantity (the QTD panel) anchors
  its Y axis at zero, so the magnitude is honest and a small change is not
  exaggerated.
- **X axis:** show only the time markers needed to read the trend - target
  4-10 ticks total, never one per data point. With 16 historical quarters,
  render roughly one tick per year or 6-8 evenly spaced ticks. Abbreviate
  labels (for example "Q1 '24").
- **Y axis:** even, predictable increments using round numbers. Abbreviate
  large values (`$1.2M`, not `$1,200,000`), respecting the series unit.
- **Tick marks:** always evenly spaced.
- **Tooltip:** `--surface`, `1px solid var(--rule)`, `--radius`,
  `--shadow-overlay`, 12px text. Label in Roboto 500; values in Roboto Mono.
- **Grid lines:** if present, `--rule` hairlines, kept minimal.
- **Axis text:** Roboto Mono, 11-12px, `--ink-muted`.

---

## 9. Layout and dashboard rules

From YipitData's published dashboard guidance:

- Page-level filters (search, sector) sit at the **top** of the page.
- A filter that affects a single chart sits directly **below that chart's
  title, left-aligned**.
- Always provide sensible **default filter values** - the date filter defaults
  to the full available range.
- The **landing page** is a fast overview that helps the user act; it is never
  documentation.
- **One purpose per page.** Minimize content and options to reduce cognitive
  load.
- Keep **backgrounds consistent**; do not wrap content in shadowed cards.

---

## 10. Accessibility

- Text contrast meets WCAG AA: 4.5:1 for normal text, 3:1 for large text and UI
  components.
- `--accent` `#197F9F` on white is approximately 3.9:1. Use it only for fills,
  borders, focus rings, large text, and the chart line - never for normal-size
  body text. Interactive text uses `--link` `#0D4753` (~9:1).
- `--ink-muted` `#616767` on `--surface` and `--canvas` is approximately 5:1 -
  acceptable for secondary text.
- `--ink-subtle` `#9AA3A5` on white is approximately 2.6:1 and fails AA for
  text. Use it only for placeholder text (a real `<label>` is always present
  too) and disabled controls, never for content such as a caption.
- Every interactive element has a visible focus state (section 6).
- Never encode meaning by color alone. Pair color with text, shape, or position
  (history and QTD live in separate, titled panels).
- All controls are reachable and operable by keyboard.

---

## 11. Anti-patterns

Do not:

- Use the Tailwind default palette, or any color outside section 3.
- Use decorative gradients (gradient buttons or backgrounds), glassmorphism, or
  background blur. A subtle area fill under a chart line - a soft vertical fade
  of the series color - is a functional data-visualization element, not
  decoration, and is allowed.
- Put drop shadows on cards, surfaces, or buttons. The only shadow is
  `--shadow-overlay`.
- Use emoji, or decorative icons. Any icon is functional and from one
  consistent set.
- Introduce type sizes or weights outside section 4.
- Carry more than one accent hue.
- Box every group of content. Prefer whitespace and hairline rules.
