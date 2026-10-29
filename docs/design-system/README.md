# CultureQuest Lo-fi

The low-fidelity design system for **CultureQuest**, a mobile-responsive travel-prep app built in Python with Flet (Material 3). It sets the shared rules for the Pass 2 wireframes: grayscale color roles, the Material 3 type scale, spacing, shape, breakpoints, icons, and a component sheet in which every component maps to a standard Flet control.

This round settles **layout and hierarchy** before Phase 5 (Flet UI). Brand color, illustration and visual polish are out of scope. The final palette arrives later as one `color_scheme_seed`, so nothing here may depend on hue.

## Principles

- **Content first.** Phrases and notes are the product; chrome stays quiet. Flat `surface-container` cards, no shadows, no decoration.
- **Scannable.** Clear headings, short blocks, one primary action per screen. The filled `accent` button appears at most once per screen.
- **Honest data.** Missing values read "Unavailable". Sources and review dates are always visible.
- **Same structure at every width.** Desktop reflows the phone layout; it never adds features.
- **Buildable in Flet.** Only standard controls: no custom drawing, overlapping layers or bespoke animation.

## Content rules

- Missing values show the word **Unavailable**, never a blank, dash or zero.
- Every cultural note shows its source and review date ("Reviewed Oct 2026"); every phrase card shows its source.
- Cultural notes describe common practice, not universal rules, and name the community or region where relevant.
- Romanization appears only for unfamiliar scripts (Japanese, Korean). French, Spanish and Portuguese show the original and English only.
- Country data credits REST Countries on the profile and in About.
- Every photo shows its credit directly underneath (photographer, license, source); About credits Wikimedia Commons and the flag CDN.
- Sentence case for every label and heading. No all-caps.

## Color roles

Wireframes use the grayscale roles only. `accent` is the single hue, reserved for focus, selection and the primary button.

| Role | Value | Use |
| --- | --- | --- |
| `surface` | #FFFFFF | Page background |
| `surface-container` | #F2F2F2 | Cards, field fills, nav bar and rail |
| `surface-container-high` | #E6E6E6 | Selected chip, nav indicator, matrix header, badge |
| `outline` | #BDBDBD | Dividers, hairlines, placeholder boxes (decorative only) |
| `control-border` | = `on-surface-variant` | Borders of chips and outlined buttons |
| `on-surface-variant` | #616161 | Secondary text, captions, sources |
| `on-surface` | #1F1F1F | Primary text and icons |
| `accent` (placeholder) | #3D5AFE | Focus ring, selected state, primary button |
| `warning-container` | #FFF4D6 | Offline and partial-mode banners |
| `error-container` | #FDE7E7 | Error view |

**Contrast.** All text pairs pass WCAG AA (4.5:1): `on-surface-variant` is 6.2:1 on `surface` and 4.9:1 on `surface-container-high`; white on `accent` is 5.1:1. `outline` (1.9:1) is decorative only: dividers and hairlines. Interactive control borders use `control-border`, an alias of `on-surface-variant` at 6.2:1, which meets the 3:1 non-text target. In Flet, set it as the chip and outlined-button `side` color.

## Typography

Noto Sans, with **Noto Sans JP** and **Noto Sans KR** as fallbacks so Japanese and Korean render; Noto Sans covers French and Portuguese accents. Fonts load from Google Fonts. Sizes follow the Material 3 scale, in pixels.

| Token | Size / line height | Weight | Use |
| --- | --- | --- | --- |
| Headline M | 28 / 36 | 400 | Country name on profile |
| Headline S | 24 / 32 | 400 | Screen titles |
| Title L | 22 / 28 | 500 | Native-script phrase text |
| Title M | 16 / 24 | 500 | Section headings, card titles |
| Body L | 16 / 24 | 400 | Cultural note text |
| Body M | 14 / 20 | 400 | Default body, list rows |
| Label L | 14 / 20 | 500 | Buttons, chips, tabs |
| Label M | 12 / 16 | 500 | Captions, sources, review dates |

**Phrase hierarchy:** native script (Title L), then romanization (Body M italic, the `romanization` style), then English meaning (Body M, `on-surface-variant`).

## Spacing, shape, elevation

| Token | Values |
| --- | --- |
| Spacing scale (4px base) | 4, 8, 12, 16, 24, 32, 48 (`space-4` … `space-48`) |
| Page margin | 16 phone, 24 desktop |
| Gap between cards | 12 phone, 16 desktop |
| Corner radius | `radius-sm` 8 for inputs and small elements; `radius-md` 12 for cards; `radius-full` for chips, buttons, nav indicator |
| Elevation | Flat; cards use `surface-container` fill, not shadows |
| Minimum touch target | 48 × 48 |
| Max content width (desktop) | 1200, centered; Explore list and About use a 720 reading column |

## Breakpoints and artboards

| Name | Width | Navigation | Layout |
| --- | --- | --- | --- |
| Compact | under 768px | Bottom navigation bar | Single column |
| Expanded | 768px and up | Left navigation rail | Up to two columns |

768px matches the `md` breakpoint of Flet's `ResponsiveRow`, so columns are set as `col={"xs": 12, "md": 6}`. Artboards: phone 390 × 844, desktop 1280 × 800.

## Iconography

Material Symbols, outlined, 24px (18px inside chips and text buttons): `explore` (Explore), `compare_arrows` (Compare), `info` (About, partial mode, uncurated), `search`, `filter_list`, `close`, `cloud_off` (offline), `error` (error view), `open_in_new` (external source). Standard Material controls also use `arrow_back`, `chevron_right`, `arrow_drop_down`, `check` and `add`. Imagery adds `image` (photo placeholder) and `location_on` (map marker). No custom icons, and no emoji: flags are images (FlagImage). Every icon-only button has a tooltip.

## Components

Every screen is built from these, and each maps to one standard Flet control.

| Component | Flet control | Used on |
| --- | --- | --- |
| NavigationBar | `NavigationBar` | All screens, compact |
| NavigationRail | `NavigationRail` | All screens, expanded |
| AppBar | `AppBar` | Profile, Compare, About |
| Button | `FilledButton`, `OutlinedButton`, `TextButton` | Throughout |
| SourceLink | `TextButton` + `open_in_new` | Profile, About |
| SearchField | `TextField` (filled, search icon) | Explore, Compare picker |
| RegionDropdown | `Dropdown` | Explore |
| CategoryChips | `Chip` (filter) in a scrolling `Row` | Profile phrases |
| CompareTray | `Chip` (input, with delete) | Compare |
| CountryRow | `ListTile` | Explore, Compare picker |
| CuratedBadge | small `Container` label | Explore rows |
| FactCard | `Card` + `Column` | Profile |
| PhraseCard | `Card` | Profile |
| CulturalNoteCard | `Card` | Profile |
| BarChart | `flet_charts.BarChart` | Compare |
| LanguageMatrix | `DataTable` | Compare |
| Banner | `Banner` | Global, top of content |
| Loading | `ProgressRing` + text | App start |
| EmptyState | icon + text + optional button | Explore, Compare, Profile |
| ErrorView | icon plate + text + `FilledButton` | App start, no data |
| FlagImage | `Image` (4:3) with placeholder | Explore rows, Compare picker, Profile header |
| PhotoHeader | `Image` (cover) + credit `Text` | Profile, curated countries only |
| ProfileTabs | `Tabs` | Profile, compact width only |
| MapCard (stretch goal) | `flet-map` `Map` in a `Card` | Profile, under Key facts |

## Accessibility

- Text contrast at least 4.5:1 (WCAG AA); control borders at least 3:1 via `control-border`.
- Never color alone: the language matrix uses check marks, selected chips show a check icon, the selected nav destination has an indicator pill.
- Every icon-only button has a text label or tooltip.
- Touch targets at least 48 × 48.
- Chart values are printed as labels, readable without hovering.

## Out of scope

User accounts, saved items, a world map on Explore, booking and automatic translation. Brand color and illustration wait for a later round.

## Imagery decisions

- **Flags:** images from the REST Countries flag CDN, never emoji.
- **Photos:** one curated photo per curated country from Wikimedia Commons, recorded in `photos.csv` and credited under the photo. Uncurated profiles show the flag only.
- **Map:** a profile MapCard is a stretch goal after the five-country MVP (M2).
- **Offline:** flags, photos and map tiles need the network; each falls back to a placeholder, so the layout never breaks.
