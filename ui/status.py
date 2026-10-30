"""Whole-screen states (Loading, Error) and the status banners (offline, partial mode)."""

import flet as ft

from ui import components as ui
from ui import messages as msg
from ui import theme
from ui.components import Handler

C = ft.Colors


def _centered(controls: list[ft.Control]) -> ft.Container:
    return ft.Container(
        ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=theme.SPACE_L,
            tight=True,
        ),
        alignment=ft.Alignment.CENTER,
        padding=theme.SPACE_XL,
        expand=True,
    )


def loading_view() -> ft.Container:
    """Shown while the country data loads at startup or on Retry."""
    ring = ft.ProgressRing(
        width=theme.LOADING_RING,
        height=theme.LOADING_RING,
        color=C.PRIMARY,
        bgcolor=C.SECONDARY_CONTAINER,
        semantics_label=msg.LOADING,
    )
    return _centered([ring, ui.text(msg.LOADING, color=C.ON_SURFACE_VARIANT)])


def error_view(error_code: str | None, on_retry: Handler) -> ft.Container:
    """Shown when there is no country data at all (no connection and no saved data)."""
    plate = ft.Container(
        ft.Icon(ft.Icons.CLOUD_OFF_OUTLINED, color=C.ON_ERROR_CONTAINER),
        width=theme.ERROR_PLATE,
        height=theme.ERROR_PLATE,
        bgcolor=C.ERROR_CONTAINER,
        shape=ft.BoxShape.CIRCLE,
        alignment=ft.Alignment.CENTER,
    )
    message = ft.Column(
        [
            ui.text(msg.ERROR_TITLE, theme.TITLE_M, text_align=ft.TextAlign.CENTER),
            ui.text(
                msg.error_reason(error_code),
                color=C.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=theme.SPACE_XS,
        tight=True,
        width=theme.EMPTY_TEXT_WIDTH,
    )
    retry = ft.Container(ui.filled_button(msg.RETRY, on_retry), padding=ft.Padding.only(top=8))
    return _centered([plate, message, retry])


def offline_banner(fetched_at: str | None, on_retry: Handler, on_dismiss: Handler):
    """Country data came from the saved copy because the live fetch failed (US-08)."""
    return ui.banner(
        ft.Icons.CLOUD_OFF_OUTLINED,
        msg.offline_banner_text(fetched_at),
        [(msg.RETRY, on_retry), (msg.DISMISS, on_dismiss)],
    )


def partial_banner(on_dismiss: Handler):
    """The curated CSVs failed to load; country facts still work."""
    return ui.banner(ft.Icons.INFO_OUTLINE, msg.PARTIAL_BANNER, [(msg.DISMISS, on_dismiss)])
