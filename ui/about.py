"""About screen: what the app does, where the data came from, and the credits (TR-05)."""

import flet as ft

from src.state import AppState
from ui import components as ui
from ui import messages as msg
from ui import theme


def about_view(state: AppState, wide: bool) -> ft.Control:
    margin = theme.MARGIN_DESKTOP if wide else theme.MARGIN_PHONE
    status = ui.facts_card(
        msg.DATA_STATUS,
        [
            (msg.SOURCE, msg.source_text(state.source)),
            (msg.FETCHED, msg.date_text(state.fetched_at)),
        ],
    )
    sources = ft.Column(
        [
            ui.section_title(msg.SOURCES_TITLE),
            ft.Column(
                [
                    ui.source_row(label, detail, url, first=index == 0)
                    for index, (label, detail, url) in enumerate(msg.SOURCES)
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ],
        spacing=theme.SPACE_S,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
    culture_note = ft.Column(
        [ui.section_title(msg.CULTURE_NOTE_TITLE), ui.text(msg.CULTURE_NOTE)],
        spacing=theme.SPACE_S,
    )
    column = ft.Column(
        [
            ui.text(msg.ABOUT_TITLE, theme.HEADLINE_S),
            ui.text(msg.ABOUT_INTRO, theme.BODY_L),
            status,
            sources,
            culture_note,
            ui.caption(msg.BUILT_BY),
        ],
        spacing=theme.SPACE_XL,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
    content = ft.Container(
        column,
        width=theme.ABOUT_MAX_WIDTH if wide else None,
        padding=ft.Padding.only(left=margin, top=theme.TITLE_TOP_PADDING, right=margin, bottom=32),
    )
    body = ft.Row([content], alignment=ft.MainAxisAlignment.CENTER) if wide else content
    return ft.Column([body], scroll=ft.ScrollMode.AUTO, expand=True)
