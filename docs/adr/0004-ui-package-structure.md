# ADR-0004: Top-level `ui/` package with a shell, one file per screen, and pure messages

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Jordon Draper

## Context

Phase 5 builds the Flet presentation layer on top of the pure domain functions and `AppState` from Phase 4. The architecture planned the UI under `src/ui/` with route-based navigation. Three things needed deciding before writing screens: where UI code lives, how navigation works, and how user-facing text is kept testable. The course requires programmer-defined functions with data transformation, and the grading relies on a working app plus clear code.

## Options considered

- **UI inside `src/ui/`:** keeps one package, but mixes Flet code into the package the tests treat as UI-free.
- **Top-level `ui/` package:** `src/` holds data access, domain logic and state; `ui/` holds everything that imports Flet.
- **Navigation with Flet routes and views:** URL-like routes (`/country/JP`) and a view stack. Useful in a browser; extra machinery in a desktop app with no address bar.
- **Navigation in one shell object:** `AppShell` stores the selected destination and the open profile, and rebuilds the frame when they change.

## Decision

- UI code lives in a top-level **`ui/`** package: `shell.py` (startup flow, navigation, banners, phone/desktop layout), one file per screen (`explore.py`, `profile.py`, `compare.py`, `about.py`, `status.py`), `components.py` (one builder per component), `theme.py` (design values, ADR-0005) and `messages.py`.
- **`AppShell` handles navigation** without routes. The profile is a detail screen with a back arrow, opened from Explore or from a Compare tray chip.
- **All user-facing text and formatting** (population, dates, error reasons, labels) lives in `ui/messages.py` as **pure functions with unit tests**.
- The real loader, **`load_app_data()`**, lives in `src/loaders.py` and is injected into `AppState`; startup and Retry both go through `AppState.reload()`.

## Consequences

- `src/` stays free of Flet, so `pytest` covers it without a UI, and the dependency direction (presentation → domain) is visible in the folder layout.
- Formatting rules are tested like domain code, while screens are checked with screenshots at 390 and 1280px and the manual checklist.
- There are no deep links into a profile. That is acceptable for a desktop app; routes could be added later inside `AppShell` without changing the screens.
- Screens are small classes that keep their own controls, so search text, chips and tabs survive navigation and window resizes.
