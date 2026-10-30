"""The app frame: startup flow, navigation, banners and the phone/desktop layout.

AppShell decides which screen is visible and rebuilds the frame when the user navigates
or the window crosses the 768 px breakpoint. The screens keep their own controls, so
search text, filters and selections survive a rebuild.
"""

import flet as ft

from src.constants import SOURCE_CACHE
from src.state import AppState
from ui import messages as msg
from ui import status, theme
from ui.about import about_view
from ui.compare import CompareScreen
from ui.explore import ExploreScreen
from ui.profile import ProfileScreen

C = ft.Colors

EXPLORE, COMPARE, ABOUT = 0, 1, 2
_DESTINATIONS = (
    (msg.NAV_EXPLORE, ft.Icons.EXPLORE_OUTLINED, ft.Icons.EXPLORE),
    (msg.NAV_COMPARE, ft.Icons.COMPARE_ARROWS, ft.Icons.COMPARE_ARROWS),
    (msg.NAV_ABOUT, ft.Icons.INFO_OUTLINE, ft.Icons.INFO),
)


class AppShell:
    def __init__(self, page: ft.Page, state: AppState) -> None:
        self.page = page
        self.state = state
        self.tab = EXPLORE
        self.loading = True
        self.offline_dismissed = False
        self.partial_dismissed = False
        self.explore = ExploreScreen(state, on_open=self.open_profile)
        self.compare = CompareScreen(state, page, on_open=self.open_profile, on_change=self.render)
        self.profile: ProfileScreen | None = None
        self.nav: ft.NavigationBar | ft.NavigationRail | None = None
        self.wide = theme.is_wide(page.width)
        page.on_resize = self._on_resize

    # --- Startup and Retry ---

    def load(self, event: ft.Event | None = None) -> None:
        """Show Loading, load the data, then show Explore or the Error view."""
        self.loading = True
        self.render()
        self.state.reload()
        self.loading = False
        self.offline_dismissed = self.partial_dismissed = False
        self.profile = None
        self.explore.refresh_data()
        self.render()

    # --- Navigation ---

    def open_profile(self, code: str) -> None:
        self.profile = ProfileScreen(
            self.state, code, on_back=self._close_profile, on_compare=self.update_badge
        )
        self.render()

    def _close_profile(self, event: ft.Event | None = None) -> None:
        self.profile = None
        self.render()

    def _on_nav(self, event: ft.Event) -> None:
        self.tab = event.control.selected_index
        self.profile = None
        self.render()

    def _on_resize(self, event: ft.Event) -> None:
        wide = theme.is_wide(self.page.width)
        if wide != self.wide:  # only re-lay out when crossing the breakpoint
            self.wide = wide
            self.render()

    # --- Building the frame ---

    def render(self) -> None:
        page = self.page
        self.wide = theme.is_wide(page.width)
        if self.loading or not self.state.countries:
            view = (
                status.loading_view()
                if self.loading
                else status.error_view(self.state.fetch_error, self.load)
            )
            self.nav = None
            page.navigation_bar = None
            page.controls = [ft.SafeArea(view, expand=True)]
            page.update()
            return

        content = ft.Column(
            [*self._banners(), ft.Container(self._screen(), expand=True)],
            spacing=0,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        if self.wide:
            self.nav = self._rail()
            page.navigation_bar = None
            root: ft.Control = ft.Row(
                [self.nav, content],
                spacing=0,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        else:
            self.nav = self._nav_bar()
            page.navigation_bar = self.nav
            root = content
        page.controls = [ft.SafeArea(root, expand=True)]
        page.update()

    def _screen(self) -> ft.Control:
        if self.profile:
            return self.profile.view(self.wide)
        if self.tab == EXPLORE:
            return self.explore.view(self.wide)
        if self.tab == COMPARE:
            return self.compare.view(self.wide)
        return about_view(self.state, self.wide)

    def _banners(self) -> list[ft.Control]:
        banners = []
        if self.state.source == SOURCE_CACHE and not self.offline_dismissed:
            banners.append(
                status.offline_banner(self.state.fetched_at, self.load, self._dismiss_offline)
            )
        if self.state.content_error and not self.partial_dismissed:
            banners.append(status.partial_banner(self._dismiss_partial))
        return banners

    def _dismiss_offline(self, event: ft.Event) -> None:
        self.offline_dismissed = True
        self.render()

    def _dismiss_partial(self, event: ft.Event) -> None:
        self.partial_dismissed = True
        self.render()

    # --- Navigation bar (phone) and rail (desktop) ---

    def _badge(self, index: int) -> ft.Badge | None:
        count = len(self.state.compare_codes)
        if index != COMPARE or not count:
            return None
        return ft.Badge(label=str(count), bgcolor=C.PRIMARY, text_color=C.ON_PRIMARY)

    def _nav_bar(self) -> ft.NavigationBar:
        return ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icon(icon, badge=self._badge(index)),
                    selected_icon=ft.Icon(selected, badge=self._badge(index)),
                    label=label,
                )
                for index, (label, icon, selected) in enumerate(_DESTINATIONS)
            ],
            selected_index=self.tab,
            on_change=self._on_nav,
            bgcolor=C.SURFACE_CONTAINER,
            indicator_color=C.SECONDARY_CONTAINER,
            height=theme.NAV_BAR_HEIGHT,
            elevation=0,
        )

    def _rail(self) -> ft.NavigationRail:
        return ft.NavigationRail(
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(icon, badge=self._badge(index)),
                    selected_icon=ft.Icon(selected, badge=self._badge(index)),
                    label=label,
                )
                for index, (label, icon, selected) in enumerate(_DESTINATIONS)
            ],
            selected_index=self.tab,
            on_change=self._on_nav,
            bgcolor=C.SURFACE,
            indicator_color=C.SECONDARY_CONTAINER,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=theme.NAV_RAIL_WIDTH,
            leading=ft.Container(height=theme.SPACE_XL - theme.SPACE_S),
            group_alignment=-1.0,
        )

    def update_badge(self) -> None:
        """Refresh the Compare count after Add to compare without rebuilding the screen."""
        if self.nav is None:
            return
        # A fresh bar or rail with the new count; the screen itself is left as it is.
        if self.wide:
            new_rail = self._rail()
            row = self.nav.parent
            row.controls[row.controls.index(self.nav)] = new_rail
            self.nav = new_rail
        else:
            self.nav = self.page.navigation_bar = self._nav_bar()
        self.page.update()
