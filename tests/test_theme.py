"""Tests for the pure layout helpers in ui/theme.py."""

from ui import theme


def test_column_width_uses_max_when_window_is_wide():
    assert theme.column_width(1280, theme.EXPLORE_MAX_WIDTH) == theme.EXPLORE_MAX_WIDTH


def test_column_width_shrinks_beside_the_rail():
    # At the breakpoint, 768 - 80 px rail leaves 688 px, less than Explore's 720.
    assert theme.column_width(768, theme.EXPLORE_MAX_WIDTH) == 768 - theme.NAV_RAIL_WIDTH


def test_column_width_profile_on_a_laptop_window():
    # 1024 px is narrower than the 1104 px profile column plus the rail.
    assert theme.column_width(1024, theme.PROFILE_MAX_WIDTH) == 1024 - theme.NAV_RAIL_WIDTH


def test_column_width_never_negative_or_none():
    assert theme.column_width(None, theme.ABOUT_MAX_WIDTH) == 0
    assert theme.column_width(40, theme.ABOUT_MAX_WIDTH) == 0


def test_is_wide_at_the_breakpoint():
    assert not theme.is_wide(767)
    assert theme.is_wide(768)
    assert not theme.is_wide(None)
