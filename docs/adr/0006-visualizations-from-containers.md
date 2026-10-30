# ADR-0006: Build the population chart and language matrix from Flet containers

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Jordon Draper
- **Supersedes:** the charting note in ADR-0002 ("Charts come from `flet-charts`")

## Context

The proposal's two visualizations are a population bar chart for 2–5 selected countries and a language overlap matrix (countries as rows, API-listed languages as columns), and both must identify missing information. The hi-fi design (artboard 05) puts each value label directly above its bar, shows "Unavailable" in place of a bar when the population is missing, and pins the country column while the language columns scroll sideways on a phone.

`flet-charts` 1.0.5 renders a `BarChart` in web mode, but it has no per-bar value label: labels can only sit on an axis, so "9M" floats at the top of the chart far above a short bar. It is also a separate extension package, so it adds a dependency and a second place where the Flet API can change. `ft.DataTable` exists but can't pin a column.

## Options considered

- **`flet_charts.BarChart` + `ft.DataTable`:** least code, but the value labels and missing-value text don't match the design, and the table's first column scrolls away on a phone.
- **Plain containers for both:** each bar is a `Container` whose height is the country's share of the largest population; the matrix is a fixed country column beside a horizontally scrolling block of language columns, with the header band and row lines drawn behind it.

## Decision

Build both visualizations from plain Flet containers in `ui/charts.py`:

- `population_chart(series, wide)`: bar heights come from the pure function `bar_fractions()` in `src/processing.py` (tested). Labels come from `population_short()` ("68M", "8.7M", "1.4B", "<0.1M", "Unavailable"). Phone axis labels use the three-letter code, desktop uses names. The whole chart has one screen-reader sentence from `population_chart_label()`.
- `language_matrix(matrix)`: pinned country column, scrolling language columns, `check_circle` marks with the screen-reader label "Listed".

`flet-charts` is removed from `requirements.txt`.

## Consequences

- The visuals match the hi-fi exactly and use only `theme.py` values and color roles.
- The scaling and label logic are pure functions with unit tests, so the chart's numbers are tested like the rest of the domain code.
- One fewer dependency; nothing can break if the extension package changes.
- No hover tooltips or animations. The value labels already show every number, so nothing is lost for this use.
