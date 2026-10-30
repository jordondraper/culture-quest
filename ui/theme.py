"""Design values for CultureQuest: colors, fonts, type scale, spacing and shapes.

This is the only file with design values. Screens use ft.Colors role names (PRIMARY,
SURFACE, ...) and the constants below, never hex codes, so changing SEED recolors the
whole app. The values come from the "Passport teal" hi-fi canvas.
"""

import flet as ft

# --- Color ---
# Flet builds a full Material 3 color scheme (all the ft.Colors roles) from this one seed.
SEED = "#0B6E69"

# --- Fonts (files in assets/fonts/, registered in apply_theme) ---
FONT_FAMILY = "Noto Sans"
FONT_FILES = {
    "Noto Sans": "fonts/NotoSans-VariableFont.ttf",
    "Noto Sans JP": "fonts/NotoSansJP-VariableFont.ttf",
}
# Phrases in these languages need a font with their script. Phase 7 adds Korean.
_SCRIPT_FONTS = {"Japanese": "Noto Sans JP"}


def native_font(language: str) -> str | None:
    """The font for native-script text in this language, or None for the default."""
    return _SCRIPT_FONTS.get(language)


# --- Type scale (size, line height, weight) ---
# TextStyle.height is a multiple of the font size, so 36/28 means a 36 px line.
def _type(size: int, line: int, weight: ft.FontWeight, **extra) -> ft.TextStyle:
    return ft.TextStyle(size=size, height=line / size, weight=weight, **extra)


HEADLINE_M = _type(28, 36, ft.FontWeight.W_600)  # country name on the profile
HEADLINE_S = _type(24, 32, ft.FontWeight.W_600)  # screen titles
TITLE_L = _type(22, 28, ft.FontWeight.W_500)  # native-script phrase
TITLE_M = _type(16, 24, ft.FontWeight.W_500)  # section headings, card titles
BODY_L = _type(16, 24, ft.FontWeight.W_400)  # cultural note text
BODY_L_STRONG = _type(16, 24, ft.FontWeight.W_500)  # country name in the list
BODY_M = _type(14, 20, ft.FontWeight.W_400)  # default text
ROMANIZATION = _type(14, 20, ft.FontWeight.W_400, italic=True)
LABEL_L = _type(14, 20, ft.FontWeight.W_500)  # buttons, chips, tabs
LABEL_M = _type(12, 16, ft.FontWeight.W_500, letter_spacing=0.5)  # captions, sources
FLAG_CODE = _type(10, 12, ft.FontWeight.W_500)  # letters on the flag placeholder

# --- Spacing (multiples of 4) ---
SPACE_XS = 4
SPACE_S = 8
SPACE_M = 12
SPACE_L = 16
SPACE_XL = 24
SPACE_XXL = 32
SPACE_XXXL = 48

MARGIN_PHONE = 16
MARGIN_DESKTOP = 24
TITLE_TOP_PADDING = 28  # space above a screen title on phones

# --- Shape ---
RADIUS_S = 8  # inputs, dropdown
RADIUS_M = 12  # cards
RADIUS_L = 16  # desktop photo banner
RADIUS_SEARCH = 28
RADIUS_PILL = 100  # chips, buttons, badges: any value past half the height is a pill
RADIUS_FLAG_LIST = 4
RADIUS_FLAG_PROFILE = 6

# --- Sizes ---
ICON = 24
ICON_SMALL = 18  # inside chips and buttons
ICON_BADGE = 14
ICON_EMPTY = 40
BUTTON_HEIGHT = 40
CHIP_HEIGHT = 32  # input chips and the tray's Add country button
SEARCH_HEIGHT = 56
DROPDOWN_HEIGHT = 40
DROPDOWN_WIDTH = 168
TILE_MIN_HEIGHT = 72
TAB_HEIGHT = 48
TAB_INDICATOR = 3
NAV_BAR_HEIGHT = 80
NAV_RAIL_WIDTH = 80
LOADING_RING = 40
ERROR_PLATE = 64
EMPTY_TEXT_WIDTH = 320

FLAG_LIST = (40, 30)
FLAG_PROFILE_PHONE = (64, 48)
FLAG_PROFILE_DESKTOP = (80, 60)
PHOTO_HEIGHT_PHONE = 220
PHOTO_HEIGHT_DESKTOP = 320

# --- Layout ---
BREAKPOINT = 768  # page widths at or above this get the desktop layout
EXPLORE_MAX_WIDTH = 720
PROFILE_MAX_WIDTH = 1104
ABOUT_MAX_WIDTH = 720
CHART_HEIGHT_PHONE = 200
CHART_HEIGHT_DESKTOP = 240
BAR_MAX_WIDTH = 44
BAR_LABEL_SPACE = 24  # space above the tallest bar for its value label
MATRIX_ROW_HEIGHT = 48
MATRIX_COUNTRY_WIDTH = 132  # the pinned country column
MATRIX_CELL_MIN_WIDTH = 96
PICKER_WIDTH = 420
PICKER_HEIGHT = 480


def is_wide(width: float | None) -> bool:
    """True for the desktop layout (navigation rail, two-column profile)."""
    return (width or 0) >= BREAKPOINT


def column_width(page_width: float | None, max_width: int) -> float:
    """Width of a centered desktop column: max_width, or less when the window is narrower.

    Beside the navigation rail there are page_width - NAV_RAIL_WIDTH pixels. A fixed
    max_width wider than that would push the right edge off the screen.
    """
    available = (page_width or 0) - NAV_RAIL_WIDTH
    return max(min(max_width, available), 0)


# The widest centered column (Profile). Below this window width, resizing changes the
# column width, so the shell redraws; above it nothing moves.
FIT_LIMIT = PROFILE_MAX_WIDTH + NAV_RAIL_WIDTH


def apply_theme(page: ft.Page) -> None:
    """Fonts, the seed color scheme and light mode, set once in main.py."""
    page.fonts = FONT_FILES
    page.theme = ft.Theme(color_scheme_seed=SEED, font_family=FONT_FAMILY)
    page.theme_mode = ft.ThemeMode.LIGHT  # light only for v1.0
    page.bgcolor = ft.Colors.SURFACE
    page.padding = 0
    page.spacing = 0
