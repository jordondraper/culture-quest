# ADR-0005: Seed-based Material 3 theme and bundled Noto fonts

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Jordon Draper

## Context

The hi-fi design pass ("Passport teal") produced the visual target for the app: a teal Material 3 palette, Noto Sans type, flat outlined cards, and Japanese text in the phrase cards (Korean follows in Phase 7). The design needs to reach the code without hex values spread through the screens, and Japanese must render on any machine, including offline.

## Options considered

- **Hand-picked hex colors per control:** exact, but every screen would carry color values, and a palette change would touch every file.
- **One seed color with Flet's Material 3 scheme:** `ft.Theme(color_scheme_seed=...)` generates every role (`PRIMARY`, `SURFACE_CONTAINER_HIGH`, `OUTLINE_VARIANT`, …). The hi-fi palette was taken from that same scheme, so the code and the design match.
- **Fonts from Google Fonts at runtime:** Flet can't load Google Fonts CSS, and it would fail offline.
- **System fonts:** Japanese glyphs depend on the operating system and may show as empty boxes.
- **Bundled font files in `assets/fonts/`,** registered with `page.fonts`.

## Decision

- `ui/theme.py` sets **`SEED = "#0B6E69"`** and light mode. Screens use `ft.Colors` role names and theme constants only; `ui/theme.py` is the only file with design values (type scale, spacing, radii, sizes, breakpoint).
- **Noto Sans and Noto Sans JP are bundled** as variable TTF files in `assets/fonts/` (about 2 MB and 9.6 MB) with their OFL license. Phrase cards pick the script font from the phrase's language (`native_font()`). Italic romanization uses Flutter's synthesized italic, so no italic file is needed.

## Consequences

- Changing `SEED` recolors the whole app; contrast was checked on the generated roles (text pairs at least 4.5:1).
- Japanese renders identically on macOS, Windows and offline. Variable fonts give every weight the type scale uses (400, 500, 600) from one file each.
- The repository grows by about 12 MB. Noto Sans KR adds about 10 MB in Phase 7; if size becomes a problem, the CJK fonts can be subset to the characters the CSVs use.
- Dark mode is out of scope for v1.0; the seed scheme would support it later with `page.dark_theme`.
