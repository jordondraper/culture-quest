# CultureQuest — Architecture

*Living document. Started in Phase 1 (Architecture and design), October 2026.*

---

## 1. System context

This view shows CultureQuest as a single box and everything it depends on outside its boundary. Internal structure (layers, functions, screens) is covered in later sections.

```mermaid
flowchart LR
    traveler["Traveler"] <-->|"search, browse, compare"| app["CultureQuest app<br/>Python + Flet"]
    env[/".env<br/>REST_COUNTRIES_API_KEY"/] -.->|"API key, read at startup"| app
    api["REST Countries API v5"] -->|"HTTPS + bearer token<br/>paginated JSON"| app
    csv[("phrases.csv<br/>culture.csv")] -->|"UTF-8 CSV, read-only"| app
    app <-->|"write after fetch, read on failure<br/>raw records + fetched_at (UTC)"| cache[("data/cache/countries.json<br/>3-day limit, gitignored")]
    sources["Wikivoyage, UNESCO,<br/>official tourism boards"] -.->|"manual curation, design time"| csv

    classDef appBox fill:#EEEDFE,stroke:#534AB7,color:#3C3489
    classDef designTime stroke-dasharray: 5 5
    class app appBox
    class env,sources designTime
```

Solid arrows are runtime data flows. Dashed arrows are configuration or manual, design-time inputs.

### Boundary notes

**Direction of data.** The REST Countries API and the curated CSVs are read-only from the app's side. The local cache is the only store the app both writes and reads: it writes after a successful API fetch and reads when the API is unavailable.

**Cache format.** One JSON file, `data/cache/countries.json`:

```json
{"fetched_at": "2026-10-27T19:42:00Z", "source": "restcountries-v5", "records": []}
```

- `fetched_at` is stored inside the file in UTC, rather than relying on the file's modified time, so the 3-day age check is explicit and testable.
- `records` holds **raw** API records. Live and cached data both pass through `normalize_countries()`, so there is a single transformation path.
- Per the REST Countries terms, cached data older than 3 days is not used, and the cache folder is never committed or submitted.

**Configuration.** The API key is read from `.env` at startup. A missing or invalid key is the most likely failure on another machine, so the app reports it with a clear message instead of crashing (see Section 4, Flows).

**Curated content.** Wikivoyage phrasebooks, UNESCO Intangible Cultural Heritage lists, and official tourism boards are researched manually and recorded in the CSVs with a source URL and review date. The app never contacts these sites at runtime. Their attribution, along with REST Countries attribution, appears on the in-app Credits screen.

**Data source alternative (pending ADR-0001).** If the `mledoze/countries` dataset plus the World Bank API is approved, only the REST Countries box changes: it splits into a committed JSON file and a keyless API, and the `.env` input and 3-day cache rule no longer apply. Nothing inside the app boundary changes, which confirms the data-access layer is isolated correctly.

**Future (US-10, stretch).** Saved items would add a separate, writable local store for user data. It is not shown here because it is out of MVP scope.

---

## 2. Components

*To do: the three layers, the five functions, and `AppState`.*

## 3. Data contracts

Contracts define what each function returns in every situation, so callers never have to guess. All contracts use plain dictionaries. Keys are always present, even when a value is `None`.

### 3.1 Country dictionary

Produced by `normalize_countries()`. All countries are stored in one dictionary keyed by country code (`countries["JP"]`).

```python
{
    "code": "JP",              # ISO alpha-2, uppercase: the join key
    "code3": "JPN",            # ISO alpha-3
    "name": "Japan",
    "official_name": "Japan",
    "capitals": ["Tokyo"],     # always a list; may be empty
    "region": "Asia",
    "subregion": "Eastern Asia",
    "languages": [{"code": "jpn", "name": "Japanese"}],
    "currencies": [{"code": "JPY", "name": "Japanese yen", "symbol": "¥"}],
    "population": 125124989,   # int, or None if missing
    "flag": "🇯🇵",
}
```

- Source-specific field names stay inside `normalize_countries()`.
- Missing data is `None` in the data layer; the UI displays "Unavailable."

### 3.2 `fetch_country_data()` result

```python
{"records": [...], "source": "live",  "fetched_at": "2026-10-28T01:33:00Z", "error": None}
{"records": [...], "source": "cache", "fetched_at": "2026-10-26T18:00:00Z", "error": "network"}
{"records": [],    "source": "none",  "fetched_at": None,                   "error": "no_api_key"}
```

| Key | Type | Purpose |
|---|---|---|
| `records` | list of raw API dictionaries | The data; empty list when nothing is available |
| `source` | `"live"`, `"cache"`, or `"none"` | Where the data came from; the UI checks this first |
| `fetched_at` | UTC ISO timestamp string, or `None` | Drives the "Showing saved data from…" notice |
| `error` | error code, or `None` | Why the live fetch failed |

**Error codes (closed list):** `no_api_key`, `auth_failed` (401/403), `rate_limited` (429), `network`, `bad_response`.

**Behavior by situation**

| Situation | Result | UI shows |
|---|---|---|
| API works | `source: "live"` | Normal app |
| API fails, cache ≤ 3 days old | `source: "cache"` + error code | Normal app with a saved-data notice |
| API fails, cache > 3 days old | `source: "none"`; expired cache is deleted | Error state with Retry |
| API fails, no cache | `source: "none"` | Error state with Retry |
| No API key | Network skipped; cache used if fresh, otherwise `source: "none"` | Saved-data notice, or a setup error pointing to the README |
| Corrupted cache file | Treated as no cache; file is deleted | Same as no cache |

**Design decisions**

- **Return, don't raise, for expected failures.** Every situation above is a normal outcome for an API-dependent app, and the UI needs to display each one. Exceptions are reserved for programming errors.
- **Catch specific exceptions** (`requests.RequestException`, `json.JSONDecodeError`), never a bare `except:`, so real bugs aren't disguised as network errors.
- **Codes, not messages.** User-facing wording lives in the presentation layer, which maps each error code to text. This keeps dependencies flowing one way.
- **Records stay raw.** The caller passes them to `normalize_countries()`, so live and cached data share one transformation path.
- **Expired caches are deleted,** in line with the REST Countries prohibition on long-term storage.

### 3.3 `build_country_profile()` result

A pure function: it joins already-loaded data by country code and performs no file or network access.

```python
{
    "country": {...},   # the country dictionary from 3.1, unchanged
    "phrases": [...],   # rows from phrases.csv for this country
    "culture": [...],   # rows from culture.csv for this country
}
```

| Input | Output |
|---|---|
| Valid code, curated country | `country` plus non-empty `phrases` and `culture` lists |
| Valid code, no curated content | `country` plus two empty lists |
| Unknown code | Raises `ValueError("Unknown country code: XX")` |

**Design decisions**

- **The country is nested, not flattened,** so the country contract stays intact and UI components that accept a country dictionary work on `profile["country"]` directly.
- **Unknown codes raise.** The UI only obtains codes from the `countries` dictionary, so an unknown code indicates a bug, not a user error.
- **No curated content returns empty lists, never `None`.** This is the normal case for most countries; the UI shows an empty state.
- **Phrases are a flat list,** sorted by category order and then CSV row order. Category filtering is a separate pure function, `filter_phrases(phrases, category=None)`. Culture notes are also flat; the UI can group them by `note_type`.
- **Validate at load time, trust at join time.** `normalize_countries()` and `load_curated_content()` trim and uppercase country codes and reject invalid ones, so the join compares codes directly.
- Every phrase and culture row keeps its `source_url` and `review_date` for attribution in the UI.

### 3.4 Phrase categories

*To do: closed list of 5–7 categories (Step 3c).*

## 4. Flows

*To do: startup sequence and failure handling.*

## 5. Screens and navigation

*To do: screen list, navigation, and view states.*

## 6. Testing strategy

*To do.*
