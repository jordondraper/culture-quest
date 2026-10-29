"""AppState: everything the UI needs to remember while the app runs.

One AppState object holds the loaded data and the user's current selections. The
screens read from it and call its methods; they never fetch or load data themselves.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.constants import MAX_COMPARE, MIN_COMPARE, SOURCE_NONE

# A function with no arguments that returns {"countries", "phrases", "culture", "photos",
# "source", "fetched_at", "fetch_error", "content_error"}. main.py supplies the real one;
# tests pass a fake, so AppState never touches the network or files itself.
Loader = Callable[[], dict[str, Any]]


@dataclass
class AppState:
    loader: Loader

    # Loaded data (empty until reload() runs).
    # field(default_factory=dict) gives every AppState its own new dict; a plain
    # "= {}" default would be shared between objects.
    countries: dict[str, dict] = field(default_factory=dict)
    phrases: list[dict] = field(default_factory=list)
    culture: list[dict] = field(default_factory=list)
    photos: list[dict] = field(default_factory=list)
    source: str = SOURCE_NONE
    fetched_at: str | None = None
    fetch_error: str | None = None
    content_error: str | None = None

    # The user's selections, kept across screens and reloads.
    search_query: str = ""
    region_filter: str | None = None
    compare_codes: list[str] = field(default_factory=list)

    def reload(self) -> None:
        """Call the loader and replace all loaded data at once.

        Selections are kept, except compare codes for countries that no longer exist.
        """
        data = self.loader()  # if this raises, nothing below runs and old data stays
        self.countries = data["countries"]
        self.phrases = data["phrases"]
        self.culture = data["culture"]
        self.photos = data["photos"]
        self.source = data["source"]
        self.fetched_at = data["fetched_at"]
        self.fetch_error = data["fetch_error"]
        self.content_error = data["content_error"]
        self.compare_codes = [code for code in self.compare_codes if code in self.countries]

    def add_to_compare(self, code: str) -> bool:
        """Add a country to Compare. Returns False if it is unknown, already there,
        or the list is full."""
        if code not in self.countries or code in self.compare_codes:
            return False
        if len(self.compare_codes) >= MAX_COMPARE:
            return False
        self.compare_codes.append(code)
        return True

    def remove_from_compare(self, code: str) -> None:
        """Remove a country from Compare; does nothing if it isn't there."""
        if code in self.compare_codes:
            self.compare_codes.remove(code)

    def can_compare(self) -> bool:
        """True when 2 to 5 countries are selected, enough to draw the charts."""
        return MIN_COMPARE <= len(self.compare_codes) <= MAX_COMPARE
