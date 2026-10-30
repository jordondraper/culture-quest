"""Explore screen: search and filter the country list, then open a profile (US-01, US-02)."""

import flet as ft

from src.processing import curated_country_codes, list_regions, search_countries
from src.state import AppState
from ui import components as ui
from ui import messages as msg
from ui import theme
from ui.components import Handler

C = ft.Colors


class ExploreScreen:
    """Keeps its controls between visits, so the search text and scroll survive."""

    def __init__(self, state: AppState, on_open: Handler) -> None:
        self.state = state
        self.on_open = on_open  # called with a country code
        self.search = ui.search_field(state.search_query, self._on_search, self._on_clear)
        self.count = ui.caption("")
        self.list = ft.ListView(expand=True, spacing=0)
        self.empty = ft.Container(visible=False, expand=True)
        self.region_slot = ft.Container()  # holds the dropdown, rebuilt when data reloads
        self._tiles: dict[str, ft.Container] = {}

    def refresh_data(self) -> None:
        """Rebuild the parts that depend on loaded data: regions, tiles and the list."""
        curated = curated_country_codes(self.state.phrases)
        if self.state.region_filter not in list_regions(self.state.countries):
            self.state.region_filter = None
        self.region_slot.content = ui.region_dropdown(
            list_regions(self.state.countries), self.state.region_filter, self._on_region
        )
        # One tile per country, built once and reused while the user types.
        self._tiles = {
            code: ui.country_tile(country, code in curated, self._on_tile)
            for code, country in self.state.countries.items()
        }
        self._apply_filters()

    def view(self, wide: bool, page_width: float | None = None) -> ft.Control:
        """The screen laid out for phone or desktop width."""
        margin = theme.MARGIN_DESKTOP if wide else theme.MARGIN_PHONE
        header = ft.Container(
            ft.Column(
                [
                    ui.screen_title(msg.EXPLORE_TITLE, msg.EXPLORE_SUBTITLE),
                    self.search,
                    ft.Row(
                        [self.count, self.region_slot],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=theme.SPACE_L,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.Padding.only(
                left=margin, top=theme.TITLE_TOP_PADDING, right=margin, bottom=theme.SPACE_S
            ),
        )
        column = ft.Column([header, self.list, self.empty], spacing=0, expand=True)
        if not wide:
            return column
        # Desktop: the same layout in a centered column at most 720 px wide.
        return ft.Row(
            [ft.Container(column, width=theme.column_width(page_width, theme.EXPLORE_MAX_WIDTH))],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )

    # --- Filtering ---

    def _apply_filters(self) -> None:
        results = search_countries(
            self.state.countries, self.state.search_query, self.state.region_filter
        )
        self.list.controls = [self._tiles[country["code"]] for country in results]
        self.count.value = msg.result_count(len(results))
        self.search.suffix_icon.visible = bool(self.state.search_query)
        self.list.visible = bool(results)
        self.empty.visible = not results
        if not results:
            self.empty.content = ui.empty_state(
                ft.Icons.TRAVEL_EXPLORE,
                msg.no_results(self.state.search_query),
                msg.CLEAR_SEARCH,
                self._on_clear,
            )

    def _update(self) -> None:
        """Re-filter and redraw only the parts of the screen that change."""
        self._apply_filters()
        for control in (self.list, self.empty, self.count, self.search):
            control.update()

    # --- Event handlers ---

    def _on_search(self, event: ft.Event) -> None:
        self.state.search_query = event.control.value
        self._update()

    def _on_clear(self, event: ft.Event) -> None:
        self.state.search_query = ""
        self.search.value = ""
        self._update()

    def _on_region(self, event: ft.Event) -> None:
        self.state.region_filter = event.control.value or None  # "" means All regions
        self._update()

    def _on_tile(self, event: ft.Event) -> None:
        self.on_open(event.control.data)
