"""Reusable building blocks for the screens, one builder function per component.

Each function returns a Flet control styled from ui/theme.py. Builders take plain data
(a country dict, a phrase row) plus callbacks, and never read AppState themselves.
"""

from collections.abc import Callable

import flet as ft

from ui import messages as msg
from ui import theme

Handler = Callable[..., None]
C = ft.Colors  # short alias: the color roles appear on almost every line


# --- Text ---


def text(value: str, style: ft.TextStyle = theme.BODY_M, color=C.ON_SURFACE, **extra) -> ft.Text:
    """Text in one of the theme's type styles."""
    return ft.Text(value, style=style, color=color, **extra)


def caption(value: str, **extra) -> ft.Text:
    """Small secondary text: sources, captions, fact labels."""
    return text(value, theme.LABEL_M, C.ON_SURFACE_VARIANT, **extra)


def screen_title(title: str, subtitle: str | None = None) -> ft.Column:
    """The headline block at the top of Explore, Compare and About."""
    controls = [text(title, theme.HEADLINE_S, semantics_label=title)]
    if subtitle:
        controls.append(text(subtitle, color=C.ON_SURFACE_VARIANT))
    return ft.Column(controls, spacing=theme.SPACE_XS)


def section_title(title: str) -> ft.Text:
    return text(title, theme.TITLE_M)


# --- Surfaces ---


def card(
    controls: list[ft.Control],
    bgcolor=C.SURFACE_CONTAINER_LOWEST,
    padding: int | ft.Padding = theme.SPACE_L,
    spacing: int = theme.SPACE_M,
    **extra,
) -> ft.Container:
    """A flat card with a hairline border (no shadows anywhere in the app)."""
    return ft.Container(
        content=ft.Column(controls, spacing=spacing, tight=True),
        bgcolor=bgcolor,
        border=ft.Border.all(1, C.OUTLINE_VARIANT),
        border_radius=theme.RADIUS_M,
        padding=padding,
        **extra,
    )


def divider() -> ft.Divider:
    return ft.Divider(height=1, thickness=1, color=C.OUTLINE_VARIANT)


# --- Buttons (all pill-shaped, 40 px tall) ---


def _button_style(
    color, bgcolor=None, side: ft.BorderSide | None = None, left: int = 24, right: int = 24
):
    return ft.ButtonStyle(
        shape=ft.StadiumBorder(),
        color=color,
        icon_color=color,
        bgcolor=bgcolor,
        side=side,
        elevation=0,
        icon_size=theme.ICON_SMALL,
        # Buttons don't inherit the theme font, so name it here.
        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500, font_family=theme.FONT_FAMILY),
        padding=ft.Padding.only(left=left, right=right),
    )


def filled_button(label: str, on_click: Handler, icon=None) -> ft.FilledButton:
    """The main action of a screen (at most one per screen: Retry)."""
    return ft.FilledButton(
        label,
        icon=icon,
        on_click=on_click,
        height=theme.BUTTON_HEIGHT,
        style=_button_style(C.ON_PRIMARY, C.PRIMARY, left=16 if icon else 24),
    )


def outlined_button(label: str, on_click: Handler | None, icon=None) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        label,
        icon=icon,
        on_click=on_click,
        height=theme.BUTTON_HEIGHT,
        style=_button_style(C.PRIMARY, side=ft.BorderSide(1, C.OUTLINE), left=16 if icon else 24),
    )


def tonal_button(
    label: str,
    on_click: Handler | None,
    icon=None,
    height: int = theme.BUTTON_HEIGHT,
    disabled: bool = False,
) -> ft.FilledTonalButton:
    """Secondary action ("Add country", "In compare"); greyed out when disabled."""
    color, bgcolor = (
        (C.ON_SURFACE_VARIANT, C.SURFACE_CONTAINER_HIGH)
        if disabled
        else (C.ON_SECONDARY_CONTAINER, C.SECONDARY_CONTAINER)
    )
    return ft.FilledTonalButton(
        label,
        icon=icon,
        on_click=on_click,
        height=height,
        elevation=0,
        disabled=disabled,
        style=_button_style(color, bgcolor, left=16 if icon else 24),
    )


def text_button(
    label: str, on_click: Handler | None = None, icon=None, url: str | None = None, color=C.PRIMARY
) -> ft.TextButton:
    return ft.TextButton(
        label,
        icon=icon,
        on_click=on_click,
        url=url,
        height=theme.BUTTON_HEIGHT,
        style=_button_style(color, left=12, right=12),
    )


def link_button(label: str, url: str) -> ft.TextButton:
    """A short text link that opens a web page, with the open_in_new icon after it."""
    return ft.TextButton(
        content=ft.Row(
            [
                text(label, theme.LABEL_L, C.PRIMARY),
                ft.Icon(ft.Icons.OPEN_IN_NEW, size=theme.ICON_SMALL, color=C.PRIMARY),
            ],
            spacing=theme.SPACE_XS,
            tight=True,
        ),
        url=url,
        tooltip=url,
        height=32,
        style=ft.ButtonStyle(shape=ft.StadiumBorder(), padding=ft.Padding.symmetric(horizontal=8)),
    )


def compare_button(status: str, on_click: Handler) -> ft.Column:
    """The Add to compare button in its three states: "add", "in" or "full"."""
    if status == "in":
        button = tonal_button(msg.IN_COMPARE, on_click, ft.Icons.CHECK)
        return ft.Column([button], tight=True)
    if status == "full":
        button = ft.FilledButton(
            msg.COMPARE_FULL,
            icon=ft.Icons.BLOCK,
            disabled=True,
            height=theme.BUTTON_HEIGHT,
            style=_button_style(C.ON_SURFACE_VARIANT, C.SURFACE_CONTAINER_HIGH, left=16),
        )
        return ft.Column(
            [button, caption(msg.COMPARE_FULL_HINT)], spacing=theme.SPACE_S, tight=True
        )
    return ft.Column([outlined_button(msg.ADD_TO_COMPARE, on_click, ft.Icons.ADD)], tight=True)


# --- Images ---


def flag(
    country: dict, size: tuple[int, int], radius: int = theme.RADIUS_FLAG_LIST
) -> ft.Container:
    """The country's flag, or a placeholder with its two-letter code when it can't load."""
    width, height = size
    placeholder = ft.Container(
        content=text(country["code"], theme.FLAG_CODE, C.ON_SURFACE_VARIANT),
        alignment=ft.Alignment.CENTER,
        bgcolor=C.SURFACE_CONTAINER_HIGHEST,
        width=width,
        height=height,
    )
    if country["flag"]:
        content = ft.Image(
            src=country["flag"],
            fit=ft.BoxFit.CONTAIN,
            width=width,
            height=height,
            error_content=placeholder,
            semantics_label=msg.flag_label(country),
        )
    else:
        content = placeholder
    return ft.Container(
        content=content,
        width=width,
        height=height,
        bgcolor=C.SURFACE_CONTAINER_LOWEST,
        border=ft.Border.all(1, C.OUTLINE_VARIANT),
        border_radius=radius,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def photo_header(photo: dict, country: dict, wide: bool) -> ft.Column:
    """The destination photo with its credit line underneath."""
    height = theme.PHOTO_HEIGHT_DESKTOP if wide else theme.PHOTO_HEIGHT_PHONE
    radius = theme.RADIUS_L if wide else 0
    fallback = ft.Container(
        content=ft.Icon(
            ft.Icons.LANDSCAPE_OUTLINED, size=theme.ICON_EMPTY, color=C.ON_SURFACE_VARIANT
        ),
        alignment=ft.Alignment.CENTER,
        bgcolor=C.SURFACE_CONTAINER_HIGH,
        height=height,
    )
    image = ft.Container(
        content=ft.Image(
            src=photo["image_url"],
            fit=ft.BoxFit.COVER,
            height=height,
            width=float("inf"),  # as wide as the space it is given
            error_content=fallback,
            semantics_label=msg.photo_label(country),
        ),
        height=height,
        border_radius=radius,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=C.SURFACE_CONTAINER_HIGH,
    )
    credit = ft.Container(
        caption(msg.photo_credit(photo)),
        padding=ft.Padding.symmetric(horizontal=0 if wide else theme.MARGIN_PHONE),
    )
    return ft.Column(
        [image, credit], spacing=theme.SPACE_S, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
    )


# --- Explore ---


def search_field(value: str, on_change: Handler, on_clear: Handler) -> ft.TextField:
    """The pill-shaped search box. The clear button shows only when there is text."""
    no_line = ft.OutlineInputBorder(
        side=ft.BorderSide(0, C.TRANSPARENT), border_radius=theme.RADIUS_SEARCH
    )
    field = ft.TextField(
        value=value,
        hint_text=msg.SEARCH_HINT,
        hint_style=ft.TextStyle(size=16, color=C.ON_SURFACE_VARIANT),
        text_style=theme.BODY_L,
        prefix_icon=ft.Icon(ft.Icons.SEARCH, color=C.ON_SURFACE_VARIANT),
        filled=True,
        fill_color=C.SURFACE_CONTAINER_HIGH,
        border=no_line,
        height=theme.SEARCH_HEIGHT,
        content_padding=ft.Padding.symmetric(horizontal=theme.SPACE_L, vertical=theme.SPACE_L),
        on_change=on_change,
    )
    field.suffix_icon = ft.IconButton(
        ft.Icons.CLOSE,
        icon_color=C.ON_SURFACE_VARIANT,
        tooltip=msg.CLEAR_SEARCH,
        on_click=on_clear,
        visible=bool(value),
    )
    return field


def region_dropdown(regions: list[str], value: str | None, on_select: Handler) -> ft.Dropdown:
    """Compact Region filter. The "All regions" option has the key "" (no filter)."""
    options = [ft.DropdownOption(key="", text=msg.ALL_REGIONS)]
    options += [ft.DropdownOption(key=region, text=region) for region in regions]
    return ft.Dropdown(
        value=value or "",
        options=options,
        on_select=on_select,
        width=theme.DROPDOWN_WIDTH,
        height=theme.DROPDOWN_HEIGHT,
        dense=True,
        text_style=theme.LABEL_L,
        border=ft.OutlineInputBorder(
            side=ft.BorderSide(1, C.OUTLINE), border_radius=theme.RADIUS_S
        ),
        filled=False,
        content_padding=ft.Padding.symmetric(horizontal=theme.SPACE_M),
        enable_search=False,
        menu_height=360,
    )


def phrases_badge() -> ft.Container:
    """Small pill showing that a country has curated phrases."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.TRANSLATE, size=theme.ICON_BADGE, color=C.ON_PRIMARY_CONTAINER),
                text(msg.PHRASES_BADGE, theme.LABEL_M, C.ON_PRIMARY_CONTAINER),
            ],
            spacing=theme.SPACE_XS,
            tight=True,
        ),
        bgcolor=C.PRIMARY_CONTAINER,
        border_radius=theme.RADIUS_PILL,
        height=20,
        padding=ft.Padding.only(left=6, right=8),
    )


def country_tile(country: dict, curated: bool, on_click: Handler) -> ft.Container:
    """One row of the country list: flag, name (+ Phrases badge), region · capital."""
    name_row = [text(country["name"], theme.BODY_L_STRONG, no_wrap=False)]
    if curated:
        name_row.append(phrases_badge())
    details = ft.Column(
        [
            ft.Row(name_row, spacing=theme.SPACE_S, wrap=True),
            text(msg.tile_subtitle(country), color=C.ON_SURFACE_VARIANT),
        ],
        spacing=0,
        expand=True,
    )
    row = ft.Row(
        [
            flag(country, theme.FLAG_LIST),
            details,
            ft.Container(
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C.ON_SURFACE_VARIANT),
                width=48,
                height=48,
                alignment=ft.Alignment.CENTER,
            ),
        ],
        spacing=theme.SPACE_L,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(
        content=row,
        # 12 above and below the 48 px chevron box gives the 72 px minimum row height.
        padding=ft.Padding.only(
            left=theme.SPACE_L, top=theme.SPACE_M, right=theme.SPACE_XS, bottom=theme.SPACE_M
        ),
        border=ft.Border.only(bottom=ft.BorderSide(1, C.OUTLINE_VARIANT)),
        on_click=on_click,
        ink=True,
        data=country["code"],
    )


# --- Profile ---


def facts_card(title: str, facts: list[tuple[str, str]]) -> ft.Container:
    """A card of label/value rows with dividers between them (Key facts, Data status)."""
    rows: list[ft.Control] = []
    for index, (label, value) in enumerate(facts):
        if index:
            rows.append(divider())
        rows.append(
            ft.Container(
                ft.Column([caption(label), text(value)], spacing=2, tight=True),
                padding=ft.Padding.symmetric(vertical=theme.SPACE_S),
            )
        )
    return card(
        [section_title(title), ft.Column(rows, spacing=0, tight=True)],
        spacing=theme.SPACE_XS,
    )


def key_facts(country: dict) -> ft.Container:
    """Capital, languages, currency and population in one card."""
    return facts_card(
        msg.KEY_FACTS,
        [
            (msg.CAPITAL, msg.capital_text(country["capitals"])),
            (msg.languages_label(country["languages"]), msg.languages_text(country["languages"])),
            (msg.CURRENCY, msg.currency_text(country["currencies"])),
            (msg.POPULATION, msg.population_text(country["population"])),
        ],
    )


def filter_chip(label: str, selected: bool, on_select: Handler, key: str | None) -> ft.Chip:
    """One phrase-category chip; key is the category, or None for All."""
    color = C.ON_SECONDARY_CONTAINER if selected else C.ON_SURFACE_VARIANT
    return ft.Chip(
        label=label,
        # A plain size/weight style: the theme's line height makes Chip clip its label.
        label_text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500, color=color),
        selected=selected,
        show_checkmark=True,
        check_color=C.ON_SECONDARY_CONTAINER,
        selected_color=C.SECONDARY_CONTAINER,
        bgcolor=C.TRANSPARENT,
        border_side=ft.BorderSide(1, C.TRANSPARENT if selected else C.OUTLINE),
        shape=ft.StadiumBorder(),
        padding=ft.Padding.symmetric(horizontal=theme.SPACE_S),
        label_padding=ft.Padding.symmetric(horizontal=theme.SPACE_XS),
        visual_density=ft.VisualDensity.COMPACT,
        on_select=on_select,
        data=key,
    )


def phrase_card(phrase: dict) -> ft.Container:
    """Native text, romanization (if any) and the English meaning."""
    native = text(phrase["native"], theme.TITLE_L, selectable=True)
    font = theme.native_font(phrase["language"])
    if font:
        native.font_family = font
    controls: list[ft.Control] = [native]
    if phrase["romanization"]:
        controls.append(text(phrase["romanization"], theme.ROMANIZATION, C.PRIMARY))
    controls.append(text(phrase["english"], color=C.ON_SURFACE_VARIANT))
    return card(
        controls,
        padding=ft.Padding.symmetric(horizontal=theme.SPACE_L, vertical=14),
        spacing=theme.SPACE_XS,
    )


def group_heading(category: str) -> ft.Container:
    return ft.Container(
        caption(msg.category_label(category)),
        padding=ft.Padding.only(top=theme.SPACE_S),
    )


def note_card(note: dict) -> ft.Container:
    """A cultural note: topic, summary, optional community, source link and review date."""
    controls: list[ft.Control] = [section_title(note["topic"]), text(note["summary"], theme.BODY_L)]
    if note["community"]:
        controls.append(text(note["community"], color=C.ON_SURFACE_VARIANT))
    controls.append(
        ft.Row(
            [
                link_button(msg.source_name(note["source_url"]), note["source_url"]),
                caption(msg.reviewed_text(note["reviewed_on"])),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    return card(controls, spacing=theme.SPACE_S)


def uncurated_notice() -> ft.Container:
    return card(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=C.ON_SURFACE_VARIANT),
                    ft.Column(
                        [
                            section_title(msg.UNCURATED_TITLE),
                            text(msg.UNCURATED_BODY, color=C.ON_SURFACE_VARIANT),
                        ],
                        spacing=theme.SPACE_XS,
                        expand=True,
                    ),
                ],
                spacing=theme.SPACE_M,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ],
        bgcolor=C.SURFACE_CONTAINER_LOW,
    )


def data_credit() -> ft.Row:
    """ "Country data: REST Countries ↗" at the bottom of the profile."""
    return ft.Row(
        [
            text(msg.COUNTRY_DATA, color=C.ON_SURFACE_VARIANT),
            link_button(msg.REST_COUNTRIES, msg.REST_COUNTRIES_URL),
        ],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


# --- Compare ---


def tray_chip(country: dict, on_open: Handler, on_remove: Handler) -> ft.Chip:
    """A country in the Compare tray: tap the name to open it, the x to remove it."""
    return ft.Chip(
        label=country["name"],
        label_text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500, color=C.ON_SURFACE),
        bgcolor=C.TRANSPARENT,
        border_side=ft.BorderSide(1, C.OUTLINE),
        shape=ft.StadiumBorder(),
        padding=ft.Padding.only(left=theme.SPACE_S),
        visual_density=ft.VisualDensity.COMPACT,
        delete_icon=ft.Icon(ft.Icons.CLOSE, size=theme.ICON_SMALL),
        delete_icon_color=C.ON_SURFACE_VARIANT,
        delete_icon_tooltip=msg.remove_label(country["name"]),
        on_click=on_open,
        on_delete=on_remove,
        data=country["code"],
    )


def picker_row(country: dict, added: bool, on_click: Handler | None) -> ft.Container:
    """One row in the Add country dialog; countries already in Compare show a check."""
    trailing = (
        ft.Icon(ft.Icons.CHECK_CIRCLE, color=C.PRIMARY)
        if added
        else ft.Icon(ft.Icons.ADD, color=C.ON_SURFACE_VARIANT)
    )
    return ft.Container(
        ft.Row(
            [
                flag(country, theme.FLAG_LIST),
                text(country["name"], theme.BODY_L, expand=True),
                trailing,
            ],
            spacing=theme.SPACE_L,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=theme.SPACE_S, vertical=theme.SPACE_S),
        border=ft.Border.only(bottom=ft.BorderSide(1, C.OUTLINE_VARIANT)),
        on_click=None if added else on_click,
        ink=not added,
        data=country["code"],
    )


def placeholder_box(message: str, height: int) -> ft.Container:
    """A reserved, labelled space for a visual that a later phase draws."""
    return ft.Container(
        caption(message, text_align=ft.TextAlign.CENTER),
        height=height,
        alignment=ft.Alignment.CENTER,
        bgcolor=C.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, C.OUTLINE_VARIANT),
        border_radius=theme.RADIUS_S,
    )


# --- About ---


def source_row(label: str, detail: str, url: str, first: bool) -> ft.Container:
    """One credit in the About screen's Sources and licenses list."""
    return ft.Container(
        ft.Column(
            [
                link_button(label, url),
                ft.Container(
                    text(detail, color=C.ON_SURFACE_VARIANT),
                    padding=ft.Padding.only(left=theme.SPACE_S),
                ),
            ],
            spacing=0,
            tight=True,
        ),
        padding=ft.Padding.symmetric(vertical=theme.SPACE_S),
        border=None if first else ft.Border.only(top=ft.BorderSide(1, C.OUTLINE_VARIANT)),
    )


# --- Status building blocks ---


def empty_state(
    icon, message: str, action_label: str | None = None, on_action: Handler | None = None
) -> ft.Container:
    controls: list[ft.Control] = [
        ft.Icon(icon, size=theme.ICON_EMPTY, color=C.ON_SURFACE_VARIANT),
        ft.Container(
            text(message, color=C.ON_SURFACE_VARIANT, text_align=ft.TextAlign.CENTER),
            width=theme.EMPTY_TEXT_WIDTH,
        ),
    ]
    if action_label:
        controls.append(text_button(action_label, on_action))
    return ft.Container(
        ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=theme.SPACE_M,
            tight=True,
        ),
        alignment=ft.Alignment.TOP_CENTER,
        padding=ft.Padding.only(top=theme.SPACE_XXXL, left=theme.SPACE_L, right=theme.SPACE_L),
    )


def banner(icon, message: str, actions: list[tuple[str, Handler]]) -> ft.Container:
    """A full-width status strip (offline or partial mode) at the top of the content."""
    buttons = [
        text_button(label, handler, color=C.ON_TERTIARY_CONTAINER) for label, handler in actions
    ]
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon, color=C.ON_TERTIARY_CONTAINER),
                        text(message, color=C.ON_TERTIARY_CONTAINER, expand=True),
                    ],
                    spacing=theme.SPACE_L,
                ),
                ft.Row(buttons, alignment=ft.MainAxisAlignment.END, spacing=theme.SPACE_XS),
            ],
            spacing=theme.SPACE_XS,
            tight=True,
        ),
        bgcolor=C.TERTIARY_CONTAINER,
        padding=ft.Padding.only(
            left=theme.SPACE_L, top=theme.SPACE_M, right=theme.SPACE_S, bottom=theme.SPACE_XS
        ),
    )
