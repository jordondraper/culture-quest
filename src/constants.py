"""Fixed values shared across modules.

These are settings and closed lists, not content: no country facts, phrases or
notes belong here (TR-03).
"""

from datetime import timedelta
from pathlib import Path

# --- File paths (built from this file's location, so they work from any folder) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CACHE_PATH = DATA_DIR / "cache" / "countries.json"
PHRASES_PATH = DATA_DIR / "phrases.csv"
CULTURE_PATH = DATA_DIR / "culture.csv"
PHOTOS_PATH = DATA_DIR / "photos.csv"

# --- REST Countries API ---
API_URL = "https://api.restcountries.com/countries/v5"
API_KEY_ENV_VAR = "REST_COUNTRIES_API_KEY"
API_PROVIDER = "restcountries.com v5"
PAGE_LIMIT = 100  # the API's maximum page size
MAX_PAGES = 10  # safety stop: about 250 records need only 3 pages
REQUEST_TIMEOUT_SECONDS = 10
CACHE_MAX_AGE = timedelta(days=3)  # REST Countries terms: cache at most 3 days

# --- Where the country data came from (fetch_country_data()["source"]) ---
SOURCE_LIVE = "live"
SOURCE_CACHE = "cache"
SOURCE_NONE = "none"

# --- Why the live fetch failed (fetch_country_data()["error"]) ---
ERROR_NO_API_KEY = "no_api_key"
ERROR_AUTH_FAILED = "auth_failed"  # 401 or 403
ERROR_RATE_LIMITED = "rate_limited"  # 429
ERROR_NETWORK = "network"  # no connection or timeout
ERROR_BAD_RESPONSE = "bad_response"  # anything else unexpected

ERROR_CODES = frozenset(
    {ERROR_NO_API_KEY, ERROR_AUTH_FAILED, ERROR_RATE_LIMITED, ERROR_NETWORK, ERROR_BAD_RESPONSE}
)

# --- Curated content (data/*.csv) ---
# Phrase categories in display order. A closed list: any other value in phrases.csv is an error.
PHRASE_CATEGORIES = (
    "greetings",
    "basics",
    "dining",
    "getting_around",
    "shopping",
    "emergencies",
)

# Columns each CSV must have, and which of them may be left blank.
PHRASE_COLUMNS = (
    "country_code",
    "category",
    "english",
    "native",
    "romanization",
    "language",
    "source_url",
    "reviewed_on",
)
PHRASE_OPTIONAL = frozenset({"romanization"})  # only Japanese and Korean use it

CULTURE_COLUMNS = (
    "country_code",
    "topic",
    "summary",
    "community",
    "source_url",
    "reviewed_on",
)
CULTURE_OPTIONAL = frozenset({"community"})  # blank means the practice is nationwide

PHOTO_COLUMNS = (
    "country_code",
    "image_url",
    "photographer",
    "license",
    "source_url",
)
PHOTO_OPTIONAL: frozenset[str] = frozenset()

# --- Compare screen ---
MIN_COMPARE = 2  # fewer than this shows the empty state instead of the charts
MAX_COMPARE = 5
