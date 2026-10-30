"""Country profile: key facts, phrases and cultural notes (US-03, US-04, US-05).

Phones show Phrases and Cultural notes in tabs; desktop shows two columns (2fr/3fr).
"""

import flet as ft

from src.constants import MAX_COMPARE
from src.processing import build_country_profile, curated_country_codes, group_phrases
from src.state import AppState
from ui import components as ui
from ui import messages as msg
from ui import theme
from ui.components import Handler

C = ft.Colors


class ProfileScreen:
    """One country's profile. Remembers the selected tab and phrase category."""

    def __init__(self, state: AppState, code: str, on_back: Handler, on_compare: Handler) -> None:
        self.state = state
        self.code = code
        self.on_back = on_back
        self.on_compare = on_compare  # tells the shell to update the Compare badge
        self.profile = build_country_profile(
            code, state.countries, state.phrases, state.culture, state.photos
        )
        self.country = self.profile["country"]
        self.groups = group_phrases(self.profile["phrases"])
        self.category: str | None = None  # None = All
        self.tab = 0  # phone only: 0 Phrases, 1 Cultural notes
        self.wide = False
        # Parts that change after a click, replaced in place so the scroll position stays.
        self.compare_slot = ft.Container()
        self.phrases_slot = ft.Container()
        self.tab_slot = ft.Container()

    @property
    def curated(self) -> bool:
        return bool(self.profile["phrases"] or self.profile["culture"])

    def view(self, wide: bool, page_width: float | None = None) -> ft.Control:
        self.wide = wide
        self.compare_slot.content = self._compare_button()
        self.phrases_slot.content = self._phrases_panel()
        body = self._desktop_body(page_width) if wide else self._phone_body()
        back_bar = ft.Container(
            ft.IconButton(
                ft.Icons.ARROW_BACK,
                icon_color=C.ON_SURFACE,
                tooltip=msg.BACK,
                on_click=self.on_back,
            ),
            height=64,
            padding=ft.Padding.only(left=theme.SPACE_XS if not wide else theme.SPACE_L),
            alignment=ft.Alignment.CENTER_LEFT,
            bgcolor=C.SURFACE,
        )
        return ft.Column([back_bar, body], spacing=0, expand=True)

    # --- Layouts ---

    def _phone_body(self) -> ft.Control:
        side = ft.Padding.symmetric(horizontal=theme.MARGIN_PHONE)
        sections: list[ft.Control] = []
        if self.profile["photo"]:
            sections.append(ui.photo_header(self.profile["photo"], self.country, wide=False))
        sections.append(
            ft.Container(
                ft.Column(
                    [self._header(), self.compare_slot, ui.key_facts(self.country)],
                    spacing=theme.SPACE_XL,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                padding=side,
            )
        )
        if self.curated:
            sections.append(self._tabs())
            self.tab_slot.content = self._tab_panel()
            sections.append(ft.Container(self.tab_slot, padding=side))
        else:
            sections.append(ft.Container(ui.uncurated_notice(self._curated_names()), padding=side))
        sections.append(ft.Container(ui.data_credit(), padding=side))
        return ft.Column(
            sections,
            spacing=theme.SPACE_XL,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _desktop_body(self, page_width: float | None) -> ft.Control:
        top: list[ft.Control] = []
        if self.profile["photo"]:
            top.append(ui.photo_header(self.profile["photo"], self.country, wide=True))
        top.append(
            ft.Row(
                [self._header(), self.compare_slot],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        left: list[ft.Control] = [ui.key_facts(self.country)]
        if self.curated:
            left.append(self._culture_section(with_title=True))
        left.append(ui.data_credit())
        right: list[ft.Control] = (
            [ui.section_title(msg.PHRASES), self.phrases_slot]
            if self.groups
            else [ui.uncurated_notice(self._curated_names())]
            if not self.curated
            else []
        )
        columns = ft.Row(
            [
                ft.Column(left, spacing=theme.SPACE_XXL, expand=2),
                ft.Column(right, spacing=theme.SPACE_L, expand=3),
            ],
            spacing=theme.SPACE_XXL,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        content = ft.Container(
            ft.Column(
                [*top, columns],
                spacing=theme.SPACE_XXL,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=theme.column_width(page_width, theme.PROFILE_MAX_WIDTH),
            padding=ft.Padding.only(
                left=theme.MARGIN_DESKTOP,
                top=theme.SPACE_S,
                right=theme.MARGIN_DESKTOP,
                bottom=40,
            ),
        )
        # The Row centers the content; the outer Column scrolls the whole page.
        return ft.Column(
            [ft.Row([content], alignment=ft.MainAxisAlignment.CENTER)],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # --- Parts ---

    def _curated_names(self) -> list[str]:
        """Names of the countries that have phrases, for the uncurated notice."""
        codes = curated_country_codes(self.state.phrases)
        return [
            self.state.countries[code]["name"] for code in codes if code in self.state.countries
        ]

    def _header(self) -> ft.Row:
        wide = self.wide
        lines: list[ft.Control] = [
            ui.text(self.country["name"], theme.HEADLINE_M),
            ui.text(msg.region_line(self.country), color=C.ON_SURFACE_VARIANT),
        ]
        official = msg.official_name_line(self.country)
        if official:
            lines.append(ui.text(official, color=C.ON_SURFACE_VARIANT))
        size = theme.FLAG_PROFILE_DESKTOP if wide else theme.FLAG_PROFILE_PHONE
        return ft.Row(
            [
                ui.flag(self.country, size, theme.RADIUS_FLAG_PROFILE),
                ft.Column(lines, spacing=0, tight=True, expand=not wide),
            ],
            spacing=theme.SPACE_L,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            tight=wide,
        )

    def _compare_status(self) -> str:
        if self.code in self.state.compare_codes:
            return "in"
        if len(self.state.compare_codes) >= MAX_COMPARE:
            return "full"
        return "add"

    def _compare_button(self) -> ft.Control:
        button = ui.compare_button(self._compare_status(), self._on_compare_click)
        # On phones the button sits left-aligned on its own line.
        return ft.Row([button], tight=True) if not self.wide else button

    def _tabs(self) -> ft.Control:
        tab_bar = ft.TabBar(
            tabs=[ft.Tab(label=msg.PHRASES), ft.Tab(label=msg.CULTURAL_NOTES)],
            scrollable=False,
            indicator_color=C.PRIMARY,
            indicator_thickness=theme.TAB_INDICATOR,
            indicator_size=ft.TabBarIndicatorSize.TAB,
            label_color=C.PRIMARY,
            unselected_label_color=C.ON_SURFACE_VARIANT,
            label_text_style=theme.LABEL_L,
            unselected_label_text_style=theme.LABEL_L,
            divider_color=C.OUTLINE_VARIANT,
            divider_height=1,
        )
        return ft.Tabs(
            content=ft.Container(tab_bar, height=theme.TAB_HEIGHT),
            length=2,
            selected_index=self.tab,
            on_change=self._on_tab,
        )

    def _tab_panel(self) -> ft.Control:
        if self.tab == 1:
            return self._culture_section(with_title=False)
        return self.phrases_slot

    def _phrases_panel(self) -> ft.Control:
        if not self.groups:
            return ft.Container()
        chips = [ui.filter_chip(msg.ALL_CATEGORIES, self.category is None, self._on_chip, None)]
        chips += [
            ui.filter_chip(msg.category_label(cat), self.category == cat, self._on_chip, cat)
            for cat, _ in self.groups
        ]
        chip_row = (
            ft.Row(chips, wrap=True, spacing=theme.SPACE_S, run_spacing=theme.SPACE_S)
            if self.wide
            else ft.Row(chips, scroll=ft.ScrollMode.HIDDEN, spacing=theme.SPACE_S)
        )
        blocks: list[ft.Control] = [chip_row]
        for category, phrases in self.groups:
            if self.category not in (None, category):
                continue
            if self.category is None:  # group headings only when showing every category
                blocks.append(ui.group_heading(category))
            blocks.append(self._phrase_cards(phrases))
        blocks.append(ui.caption(msg.phrase_source_text(self.profile["phrases"][0]["language"])))
        return ft.Column(
            blocks, spacing=theme.SPACE_M, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )

    def _phrase_cards(self, phrases: list[dict]) -> ft.Control:
        cards = [ui.phrase_card(phrase) for phrase in phrases]
        if self.wide:  # two-column grid on desktop
            for card in cards:
                card.col = 6
            return ft.ResponsiveRow(cards, spacing=theme.SPACE_M, run_spacing=theme.SPACE_M)
        return ft.Column(
            cards, spacing=theme.SPACE_S, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )

    def _culture_section(self, with_title: bool) -> ft.Control:
        intro = ui.text(msg.CULTURE_INTRO, color=C.ON_SURFACE_VARIANT)
        if with_title:  # desktop: heading and intro sit close together, like a subtitle
            intro = ft.Column([ui.section_title(msg.CULTURAL_NOTES), intro], spacing=theme.SPACE_XS)
        controls = [intro, *(ui.note_card(note) for note in self.profile["culture"])]
        return ft.Column(
            controls, spacing=theme.SPACE_M, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )

    # --- Event handlers ---

    def _on_compare_click(self, event: ft.Event) -> None:
        if self.code in self.state.compare_codes:
            self.state.remove_from_compare(self.code)
        else:
            self.state.add_to_compare(self.code)
        self.compare_slot.content = self._compare_button()
        self.compare_slot.update()
        self.on_compare()

    def _on_tab(self, event: ft.Event) -> None:
        self.tab = event.control.selected_index
        self.tab_slot.content = self._tab_panel()
        self.tab_slot.update()

    def _on_chip(self, event: ft.Event) -> None:
        self.category = event.control.data
        self.phrases_slot.content = self._phrases_panel()
        self.phrases_slot.update()
