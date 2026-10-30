"""Compare screen: the tray of selected countries, the Add country picker, and the
population bar chart and language matrix (US-06, US-07).
"""

import flet as ft

from src.constants import MAX_COMPARE
from src.processing import build_language_matrix, build_population_series, search_countries
from src.state import AppState
from ui import charts, theme
from ui import components as ui
from ui import messages as msg
from ui.components import Handler

C = ft.Colors


class CompareScreen:
    def __init__(self, state: AppState, page: ft.Page, on_open: Handler, on_change: Handler):
        self.state = state
        self.page = page
        self.on_open = on_open  # called with a country code
        self.on_change = on_change  # tells the shell to redraw (screen + count badge)
        self.picker = CountryPicker(state, page, on_add=self._add)

    def view(self, wide: bool) -> ft.Control:
        margin = theme.MARGIN_DESKTOP if wide else theme.MARGIN_PHONE
        sections: list[ft.Control] = [
            ui.screen_title(msg.COMPARE_TITLE, msg.COMPARE_SUBTITLE),
            self._tray(),
        ]
        if self.state.can_compare():
            sections += [self._population_section(wide), self._languages_section()]
        else:
            sections.append(
                ui.empty_state(
                    ft.Icons.COMPARE_ARROWS, msg.compare_empty_text(len(self.state.compare_codes))
                )
            )
        return ft.Column(
            [
                ft.Container(
                    ft.Column(
                        sections,
                        spacing=theme.SPACE_XL,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    padding=ft.Padding.only(
                        left=margin, top=theme.TITLE_TOP_PADDING, right=margin, bottom=32
                    ),
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # --- Parts ---

    def _tray(self) -> ft.Row:
        chips: list[ft.Control] = [
            ui.tray_chip(self.state.countries[code], self._on_chip_open, self._on_chip_remove)
            for code in self.state.compare_codes
        ]
        add = ui.tonal_button(
            msg.ADD_COUNTRY,
            self._on_add_click,
            ft.Icons.ADD,
            height=theme.CHIP_HEIGHT,
            disabled=len(self.state.compare_codes) >= MAX_COMPARE,
        )
        chips.append(add)
        return ft.Row(chips, wrap=True, spacing=theme.SPACE_S, run_spacing=theme.SPACE_S)

    def _population_section(self, wide: bool) -> ft.Control:
        series = build_population_series(self.state.countries, self.state.compare_codes)
        header = ft.Row(
            [ui.section_title(msg.POPULATION), ui.caption(msg.POPULATION_CHART_CAPTION)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        return ui.card([header, charts.population_chart(series, wide)], spacing=theme.SPACE_L)

    def _languages_section(self) -> ft.Control:
        matrix = build_language_matrix(self.state.countries, self.state.compare_codes)
        return ft.Column(
            [
                ui.section_title(msg.LANGUAGES),
                charts.language_matrix(matrix),
                ui.caption(msg.LANGUAGES_CAPTION),
            ],
            spacing=theme.SPACE_S,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    # --- Event handlers ---

    def _on_chip_open(self, event: ft.Event) -> None:
        self.on_open(event.control.data)

    def _on_chip_remove(self, event: ft.Event) -> None:
        self.state.remove_from_compare(event.control.data)
        self.on_change()

    def _on_add_click(self, event: ft.Event) -> None:
        self.picker.open()

    def _add(self, code: str) -> None:
        if self.state.add_to_compare(code):
            self.on_change()


class CountryPicker:
    """The Add country dialog: a search field over every country, using search_countries()."""

    def __init__(self, state: AppState, page: ft.Page, on_add: Handler) -> None:
        self.state = state
        self.page = page
        self.on_add = on_add  # called with a country code
        self.query = ""
        self.field = ui.search_field("", self._on_search, self._on_clear)
        self.field.autofocus = True
        self.hint = ui.caption("")
        self.list = ft.ListView(spacing=0, expand=True)
        self.dialog = ft.AlertDialog(
            title=ui.text(msg.ADD_COUNTRY_TITLE, theme.HEADLINE_S),
            content=ft.Container(
                ft.Column([self.field, self.hint, self.list], spacing=theme.SPACE_M),
                width=theme.PICKER_WIDTH,
                height=theme.PICKER_HEIGHT,
            ),
            actions=[ui.text_button(msg.DONE, self._close)],
            bgcolor=C.SURFACE_CONTAINER_LOWEST,
        )

    def open(self) -> None:
        self.query = ""
        self.field.value = ""
        self._fill()
        self.page.show_dialog(self.dialog)

    def _fill(self) -> None:
        """Show the matching countries; each row is built fresh so its check is current."""
        results = search_countries(self.state.countries, self.query)
        self.list.controls = [
            ui.picker_row(country, country["code"] in self.state.compare_codes, self._on_pick)
            for country in results
        ]
        if not results:
            self.list.controls = [
                ui.empty_state(ft.Icons.TRAVEL_EXPLORE, msg.no_results(self.query))
            ]
        self.hint.value = msg.compare_slots_text(len(self.state.compare_codes))
        self.field.suffix_icon.visible = bool(self.query)

    def _refresh(self) -> None:
        self._fill()
        self.dialog.update()

    def _on_search(self, event: ft.Event) -> None:
        self.query = event.control.value
        self._refresh()

    def _on_clear(self, event: ft.Event) -> None:
        self.query = ""
        self.field.value = ""
        self._refresh()

    def _on_pick(self, event: ft.Event) -> None:
        self.on_add(event.control.data)
        if len(self.state.compare_codes) >= MAX_COMPARE:
            self._close()  # full: nothing more can be added
        else:
            self._refresh()

    def _close(self, event: ft.Event | None = None) -> None:
        self.page.pop_dialog()
