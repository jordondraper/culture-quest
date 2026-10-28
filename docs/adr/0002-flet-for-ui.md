# ADR-0002: Flet as the UI framework

- **Status:** Accepted
- **Date:** 2026-10-27
- **Deciders:** Jordon Draper

## Context

The proposal commits to a mobile-responsive application written in Python, with two in-app visualizations and testing at phone and desktop widths. The UI must be built entirely in Python as part of a Python course, and it should feel like an app (navigation, detail screens, back behavior) rather than a data report.

## Options considered

- **Flet:** Python-only, Flutter-based controls; built-in `ResponsiveRow`, `NavigationBar`, and `NavigationRail`; charts through the separate `flet-charts` package; runs as a desktop window or in the browser. Its API changes frequently between versions.
- **NiceGUI:** Python-only web UI with good charting support and a stable API; less app-like navigation out of the box.
- **Streamlit:** fast to build and widely used for data apps, but its top-to-bottom rerun model and limited navigation make app-style screens and mobile layouts awkward.
- **Kivy:** true mobile support, but a steeper learning curve and dated styling for the time available.

## Decision

Use **Flet**, as named in the proposal. NiceGUI is the fallback if Flet hits a blocking limitation.

## Consequences

- **Pin the Flet version** in `requirements.txt`. Examples and documentation must match the pinned version (for example, `ft.run(main)` in newer releases versus `ft.app(main)` in older ones).
- Charts come from `flet-charts` (`BarChart`); the language matrix is built from `Container` cells or a `DataTable`.
- All Flet code is confined to `src/ui/` and `main.py` (architecture.md, Section 2). Switching to NiceGUI would change only those files; data access, domain logic, and `AppState` would be untouched.
- Navigation uses Flet routes, with a bottom `NavigationBar` below 768px and a `NavigationRail` at 768px and above (Section 5).
