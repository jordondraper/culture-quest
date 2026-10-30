"""The two Compare visualizations: a population bar chart and a language overlap matrix
(US-06, US-07).

Both are built from plain Flet containers, so every size and color comes from
ui/theme.py and nothing depends on a chart package (ADR-0006). The numbers come from
the pure functions build_population_series(), bar_fractions() and build_language_matrix().
"""

import flet as ft

from src.processing import bar_fractions
from ui import components as ui
from ui import messages as msg
from ui import theme

C = ft.Colors


# --- Population bar chart ---


def population_chart(series: list[dict], wide: bool) -> ft.Control:
    """One bar per country in tray order, scaled to the largest population.

    Phone labels the bars with three-letter codes (FRA); desktop uses full names.
    A missing population shows "Unavailable" where the bar would be.
    """
    height = theme.CHART_HEIGHT_DESKTOP if wide else theme.CHART_HEIGHT_PHONE
    max_bar = height - theme.BAR_LABEL_SPACE  # room for the value label above the tallest bar
    fractions = bar_fractions(series)

    bars = ft.Row(
        [_bar(entry, fraction, max_bar) for entry, fraction in zip(series, fractions, strict=True)],
        height=height,
        spacing=theme.SPACE_S,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )
    baseline = ft.Container(height=1, bgcolor=C.OUTLINE)
    axis = ft.Row(
        [
            ft.Container(
                ui.caption(
                    entry["name"] if wide else (entry["code3"] or entry["code"]),
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                ),
                expand=True,
                alignment=ft.Alignment.TOP_CENTER,
            )
            for entry in series
        ],
        spacing=theme.SPACE_S,
    )
    chart = ft.Column([bars, baseline, axis], spacing=theme.SPACE_S, tight=True)
    # Screen readers get one sentence with every value instead of the separate bars.
    return ft.Semantics(content=chart, label=msg.population_chart_label(series), container=True)


def _bar(entry: dict, fraction: float | None, max_bar: int) -> ft.Container:
    """One column of the chart: value label on top of a teal bar, bottom-aligned."""
    if fraction is None:
        content: list[ft.Control] = [_unavailable_label()]
    else:
        # At least 2 px, so a very small country still shows a sliver of bar.
        bar_height = max(round(fraction * max_bar), 2)
        content = [
            ui.text(msg.population_short(entry["population"]), theme.LABEL_M),
            ft.Container(
                width=theme.BAR_MAX_WIDTH,
                height=bar_height,
                bgcolor=C.PRIMARY,
                border_radius=ft.BorderRadius.only(
                    top_left=theme.RADIUS_S, top_right=theme.RADIUS_S
                ),
            ),
        ]
    return ft.Container(
        ft.Column(
            content,
            spacing=theme.SPACE_XS,
            # STRETCH gives the "Unavailable" label the full slot width to center in.
            horizontal_alignment=(
                ft.CrossAxisAlignment.STRETCH if fraction is None else ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.MainAxisAlignment.END,
            tight=True,
        ),
        expand=True,
        alignment=ft.Alignment.BOTTOM_CENTER,
    )


def _unavailable_label() -> ft.Stack:
    """ "Unavailable" in place of a bar, on one line.

    With five countries on a phone, a bar slot is narrower than the word, and Flutter
    would break it mid-word ("Unavaila / ble"). The label may reach a little into the
    empty gaps beside its slot instead; the neighboring bars are narrower than their
    slots, so nothing overlaps.
    """
    reach = theme.SPACE_M  # how far the label may extend past each side of its slot
    label = ft.Container(
        ui.caption(msg.UNAVAILABLE, text_align=ft.TextAlign.CENTER, no_wrap=True),
        left=-reach,
        right=-reach,
        bottom=0,
        alignment=ft.Alignment.BOTTOM_CENTER,
    )
    # The empty Container gives the Stack its height; the label is positioned over it.
    return ft.Stack(
        [ft.Container(height=theme.LABEL_M.height * theme.LABEL_M.size), label],
        clip_behavior=ft.ClipBehavior.NONE,
    )


# --- Language overlap matrix ---


def language_matrix(matrix: dict) -> ft.Control:
    """Countries as rows, listed languages as columns, a check where a country lists one.

    The country column stays pinned on the left while the language columns scroll
    sideways, so the table works on a phone. (DataTable can't pin a column.)
    """
    if not matrix["languages"]:
        return ui.caption(msg.NO_LANGUAGES)

    country_column = ft.Column(
        [_header_cell(msg.COUNTRY_COLUMN, theme.MATRIX_COUNTRY_WIDTH, align_left=True)]
        + [_name_cell(row["name"]) for row in matrix["rows"]],
        spacing=0,
    )
    language_columns = ft.Row(
        [
            ft.Column(
                [_header_cell(language, _language_width(language))]
                + [
                    _mark_cell(row["marks"][index], _language_width(language))
                    for row in matrix["rows"]
                ],
                spacing=0,
            )
            for index, language in enumerate(matrix["languages"])
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,  # sideways scroll for the language columns only
        expand=True,
    )
    table = ft.Row(
        [
            country_column,
            ft.VerticalDivider(width=1, thickness=1, color=C.OUTLINE_VARIANT),
            language_columns,
        ],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.START,
        intrinsic_height=True,
    )
    # The header band and row lines are drawn behind the table across the full width,
    # so on a wide screen they reach the right edge even when the columns don't.
    row = theme.MATRIX_ROW_HEIGHT
    background: list[ft.Control] = [
        ft.Container(left=0, right=0, top=0, height=row, bgcolor=C.SURFACE_CONTAINER_HIGH)
    ]
    background += [
        ft.Container(left=0, right=0, top=row * line, height=1, bgcolor=C.OUTLINE_VARIANT)
        for line in range(1, len(matrix["rows"]) + 1)
    ]
    return ft.Container(
        ft.Stack([*background, table]),
        bgcolor=C.SURFACE_CONTAINER_LOWEST,
        border=ft.Border.all(1, C.OUTLINE_VARIANT),
        border_radius=theme.RADIUS_S,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def _language_width(language: str) -> int:
    """Wide enough for the language name on one line (about 9 px per character)."""
    return max(theme.MATRIX_CELL_MIN_WIDTH, len(language) * 9 + 2 * theme.SPACE_L)


def _header_cell(label: str, width: int, align_left: bool = False) -> ft.Container:
    return ft.Container(
        ui.text(label, theme.LABEL_L, no_wrap=True),
        width=width,
        height=theme.MATRIX_ROW_HEIGHT,
        padding=ft.Padding.symmetric(horizontal=theme.SPACE_L),
        alignment=ft.Alignment.CENTER_LEFT if align_left else ft.Alignment.CENTER,
    )


def _name_cell(name: str) -> ft.Container:
    return ft.Container(
        ui.text(name, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
        width=theme.MATRIX_COUNTRY_WIDTH,
        height=theme.MATRIX_ROW_HEIGHT,
        padding=ft.Padding.symmetric(horizontal=theme.SPACE_L),
        alignment=ft.Alignment.CENTER_LEFT,
    )


def _mark_cell(listed: bool, width: int) -> ft.Container:
    mark = (
        ft.Icon(ft.Icons.CHECK_CIRCLE, color=C.PRIMARY, size=theme.ICON, semantics_label=msg.LISTED)
        if listed
        else None
    )
    return ft.Container(
        mark,
        width=width,
        height=theme.MATRIX_ROW_HEIGHT,
        alignment=ft.Alignment.CENTER,
    )
