"""Every piece of text the user sees, and the functions that format data for display.

Screens never build sentences or format numbers themselves; they call these functions.
Everything here is pure (plain values in, a string out), so tests/test_messages.py can
check the exact wording without starting the UI.
"""

from datetime import date, datetime
from urllib.parse import urlparse

from src.constants import (
    ERROR_AUTH_FAILED,
    ERROR_BAD_RESPONSE,
    ERROR_NETWORK,
    ERROR_NO_API_KEY,
    ERROR_RATE_LIMITED,
    MAX_COMPARE,
    SOURCE_CACHE,
    SOURCE_LIVE,
)

APP_NAME = "CultureQuest"
UNAVAILABLE = "Unavailable"

# --- Navigation ---
NAV_EXPLORE = "Explore"
NAV_COMPARE = "Compare"
NAV_ABOUT = "About"
BACK = "Back"

# --- Explore ---
EXPLORE_TITLE = "Explore"
EXPLORE_SUBTITLE = "Find a destination to prepare for."
SEARCH_HINT = "Search countries"
CLEAR_SEARCH = "Clear search"
ALL_REGIONS = "All regions"
PHRASES_BADGE = "Phrases"

# --- Profile ---
ADD_TO_COMPARE = "Add to compare"
IN_COMPARE = "In compare"
COMPARE_FULL = "Compare is full"
COMPARE_FULL_HINT = f"Maximum of {MAX_COMPARE}. Remove one in Compare to add another."
KEY_FACTS = "Key facts"
CAPITAL = "Capital"
CURRENCY = "Currency"
POPULATION = "Population"
PHRASES = "Phrases"
CULTURAL_NOTES = "Cultural notes"
ALL_CATEGORIES = "All"
CULTURE_INTRO = "Common practices; customs vary by region and community."
COUNTRY_DATA = "Country data:"
REST_COUNTRIES = "REST Countries"
REST_COUNTRIES_URL = "https://restcountries.com"
UNCURATED_TITLE = "Phrases and notes aren't available yet"
UNCURATED_BODY = (
    "CultureQuest has travel phrases and cultural notes for Japan, Mexico, France, "
    "South Korea and Brazil."
)

# --- Status ---
LOADING = "Loading country data…"
ERROR_TITLE = "Country data isn't available right now"
RETRY = "Retry"
DISMISS = "Dismiss"
PARTIAL_BANNER = "Phrases and cultural notes couldn't load. Country facts are still available."

# --- Compare ---
COMPARE_TITLE = "Compare"
COMPARE_SUBTITLE = "Choose 2 to 5 countries."
ADD_COUNTRY = "Add country"
ADD_COUNTRY_TITLE = "Add a country"
DONE = "Done"
POPULATION_CHART_CAPTION = "Millions of people"
LANGUAGES = "Languages"
LANGUAGES_CAPTION = (
    "Languages as listed by REST Countries; not every language community is represented. "
    "Scroll sideways for more."
)
CHART_PLACEHOLDER = "The population chart appears here."
MATRIX_PLACEHOLDER = "The language table appears here."

# --- About ---
ABOUT_TITLE = "About"
ABOUT_INTRO = (
    "CultureQuest helps travelers prepare for countries whose language and customs are "
    "unfamiliar. Find a destination, read its key facts, learn useful phrases and "
    "etiquette, and compare destinations side by side."
)
DATA_STATUS = "Data status"
SOURCE = "Source"
FETCHED = "Fetched"
SOURCES_TITLE = "Sources and licenses"
# (link text, what it provides, URL) for the About screen's credits list.
SOURCES = (
    ("REST Countries", "Country facts and flags", "https://restcountries.com"),
    ("Wikivoyage phrasebooks", "Phrases · CC BY-SA", "https://en.wikivoyage.org/wiki/Phrasebooks"),
    (
        "UNESCO Intangible Cultural Heritage lists",
        "Cultural notes",
        "https://ich.unesco.org/en/lists",
    ),
    (
        "Official tourism boards",
        "Cultural notes, for example JNTO for Japan",
        "https://www.japan.travel/en/",
    ),
    (
        "Wikimedia Commons",
        "Country photos · license shown with each photo",
        "https://commons.wikimedia.org/",
    ),
)
CULTURE_NOTE_TITLE = "A note on culture"
CULTURE_NOTE = (
    "Practices vary by region and community. Cultural notes are introductions, not rules."
)
BUILT_BY = "Built by Jordon Draper for IS 6495, University of Utah."

# Display names for phrase categories that aren't just the key with spaces.
_CATEGORY_LABELS = {"getting_around": "Getting around"}

# Short names for the sites our cultural notes cite. Unknown sites show their host name.
_SOURCE_NAMES = {
    "japan.travel": "JNTO",
    "ich.unesco.org": "UNESCO",
    "wikivoyage.org": "Wikivoyage",
}

_ERROR_REASONS = {
    ERROR_NETWORK: "Check your internet connection.",
    ERROR_NO_API_KEY: "The REST Countries API key is missing. Add it to the .env file.",
    ERROR_AUTH_FAILED: "The REST Countries API key wasn't accepted. Check the .env file.",
    ERROR_RATE_LIMITED: "The REST Countries request limit was reached. Try again later.",
    ERROR_BAD_RESPONSE: "REST Countries sent an unexpected response. Try again later.",
}
_UNKNOWN_ERROR = "Something went wrong. Try again."


# --- Numbers and dates ---


def population_text(population: int | None) -> str:
    """A rounded, readable population: "About 124 million", "About 1.4 billion"."""
    if population is None:
        return UNAVAILABLE
    if population >= 1_000_000_000:
        return f"About {_one_decimal(population / 1_000_000_000)} billion"
    if population >= 10_000_000:
        return f"About {round(population / 1_000_000)} million"
    if population >= 1_000_000:
        return f"About {_one_decimal(population / 1_000_000)} million"
    if population >= 10_000:
        return f"About {round(population, -3):,}"
    return f"{population:,}"  # small numbers are shown exactly


def _one_decimal(value: float) -> str:
    """1.43 -> "1.4", 2.0 -> "2" (no trailing .0)."""
    return f"{value:.1f}".removesuffix(".0")


def date_text(timestamp: str | None) -> str:
    """An ISO timestamp like "2026-10-28T15:00:00Z" as a local date: "Oct 28, 2026"."""
    if not timestamp:
        return UNAVAILABLE
    try:
        moment = datetime.fromisoformat(timestamp)
    except ValueError:
        return UNAVAILABLE
    if moment.tzinfo is not None:
        moment = moment.astimezone()  # UTC from the API -> the user's own time zone
    # Built from parts because %-d (day without a leading zero) only works on Mac/Linux.
    return f"{moment:%b} {moment.day}, {moment.year}"


def reviewed_text(reviewed_on: str) -> str:
    """ "2026-10-29" -> "Reviewed Oct 2026"."""
    try:
        day = date.fromisoformat(reviewed_on)
    except ValueError:
        return ""
    return f"Reviewed {day:%b %Y}"


# --- Status ---


def error_reason(code: str | None) -> str:
    """One sentence explaining a fetch error code from src/constants.py."""
    return _ERROR_REASONS.get(code, _UNKNOWN_ERROR)


def offline_banner_text(fetched_at: str | None) -> str:
    return f"Showing saved data from {date_text(fetched_at)}."


def source_text(source: str) -> str:
    """Where the country data came from, for the About screen."""
    if source == SOURCE_LIVE:
        return "Live from REST Countries"
    if source == SOURCE_CACHE:
        return "Saved data"
    return UNAVAILABLE


# --- Explore ---


def result_count(count: int) -> str:
    return f"{count} country" if count == 1 else f"{count} countries"


def no_results(query: str) -> str:
    return f"No countries match “{query.strip()}”."


def tile_subtitle(country: dict) -> str:
    """ "Asia · Tokyo" for a country list row; missing parts are left out."""
    capital = country["capitals"][0] if country["capitals"] else None
    return _join(country["region"], capital)


# --- Profile ---


def region_line(country: dict) -> str:
    """ "Asia · Eastern Asia" under the country name."""
    return _join(country["region"], country["subregion"])


def official_name_line(country: dict) -> str | None:
    """The official name, only when it says something the common name doesn't."""
    official = country["official_name"]
    return official if official and official != country["name"] else None


def capital_text(capitals: list[str]) -> str:
    return ", ".join(capitals) or UNAVAILABLE


def languages_label(languages: list[dict]) -> str:
    return "Language" if len(languages) <= 1 else "Languages"


def languages_text(languages: list[dict]) -> str:
    return ", ".join(language["name"] for language in languages) or UNAVAILABLE


def currency_text(currencies: list[dict]) -> str:
    """ "Japanese yen (¥)"; several currencies are joined with commas."""
    parts = [
        f"{currency['name']} ({currency['symbol']})" if currency["symbol"] else currency["name"]
        for currency in currencies
    ]
    return ", ".join(parts) or UNAVAILABLE


def category_label(category: str) -> str:
    """ "getting_around" -> "Getting around", "greetings" -> "Greetings"."""
    return _CATEGORY_LABELS.get(category, category.replace("_", " ").capitalize())


def phrase_source_text(language: str) -> str:
    return f"Source: Wikivoyage {language} phrasebook · CC BY-SA"


def source_name(url: str) -> str:
    """A short name for a cited site: "JNTO" for japan.travel, else the host name."""
    host = (urlparse(url).hostname or "").removeprefix("www.")
    for site, name in _SOURCE_NAMES.items():
        if host == site or host.endswith("." + site):
            return name
    return host or url


def photo_credit(photo: dict) -> str:
    return f"Photo: {photo['photographer']} · {photo['license']} · Wikimedia Commons"


def flag_label(country: dict) -> str:
    """Screen-reader text for a flag image."""
    return f"Flag of {country['name']}"


def photo_label(country: dict) -> str:
    return f"Photo of {country['name']}"


# --- Compare ---


def remove_label(name: str) -> str:
    return f"Remove {name}"


def compare_empty_text(count: int) -> str:
    """The instruction shown while fewer than MIN_COMPARE countries are selected."""
    if count == 0:
        return "Add 2 to 5 countries to compare population and languages side by side."
    return "Add one more country to see the comparison."


def compare_slots_text(count: int) -> str:
    """How many more countries fit, shown in the Add country dialog."""
    left = MAX_COMPARE - count
    if left <= 0:
        return COMPARE_FULL_HINT
    return f"You can add {left} more." if left > 1 else "You can add 1 more."


# --- Helpers ---


def _join(*parts: str | None) -> str:
    """Join the non-empty parts with a middle dot; "" when nothing is left."""
    return " · ".join(part for part in parts if part)
