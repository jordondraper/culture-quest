"""Pure data transformations for CultureQuest.

Nothing in this module touches the network, files, or the UI, so every function can be
tested with plain Python data.
"""

from typing import Any

from src.constants import PHRASE_CATEGORIES

Country = dict[str, Any]

# Position of each category in display order, e.g. {"greetings": 0, "basics": 1, ...}.
_CATEGORY_RANK = {category: rank for rank, category in enumerate(PHRASE_CATEGORIES)}


# --- Small helpers (private: the leading underscore means "used only in this module") ---


def _as_dict(value: Any) -> dict:
    """Return value if it is a dict, otherwise an empty dict, so .get() is always safe."""
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    """Return value if it is a list, otherwise an empty list, so loops are always safe."""
    return value if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    """Return a trimmed string, or None if the value is missing or blank.

    The v5 API marks missing text as "" rather than null, so both count as missing.
    """
    if not isinstance(value, str):
        return None
    return value.strip() or None


def _population(value: Any) -> int | None:
    """Return a non-negative int, or None for anything else."""
    # bool is a subclass of int in Python (True == 1), so rule it out explicitly.
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _capitals(raw: Any) -> list[str]:
    """Capital names, primary capital first, other capitals in API order."""
    entries = [_as_dict(item) for item in _as_list(raw)]
    entries = [entry for entry in entries if _text(entry.get("name"))]
    # sort() is stable: entries with the same key keep their original order.
    entries.sort(key=lambda entry: not _as_dict(entry.get("attributes")).get("primary", False))
    return [_text(entry["name"]) for entry in entries]


def _languages(raw: Any) -> list[dict[str, str | None]]:
    """Languages as {"code", "name"}; entries without a name are dropped."""
    languages = []
    for item in _as_list(raw):
        item = _as_dict(item)
        name = _text(item.get("name"))
        if name:
            languages.append({"code": _text(item.get("iso639_3")), "name": name})
    return languages


def _currencies(raw: Any) -> list[dict[str, str | None]]:
    """Currencies as {"code", "name", "symbol"}; entries without a name are dropped."""
    currencies = []
    for item in _as_list(raw):
        item = _as_dict(item)
        name = _text(item.get("name"))
        if name:
            currencies.append(
                {"code": _text(item.get("code")), "name": name, "symbol": _text(item.get("symbol"))}
            )
    return currencies


def _normalize_country(record: dict) -> Country | None:
    """Turn one raw v5 record into a Country dict, or None if it can't be used."""
    codes = _as_dict(record.get("codes"))
    names = _as_dict(record.get("names"))

    code = _text(codes.get("alpha_2"))
    name = _text(names.get("common")) or _text(names.get("official"))
    if code is None or name is None:
        return None  # no join key or nothing to show: skip it

    code3 = _text(codes.get("alpha_3"))
    return {
        "code": code.upper(),
        "code3": code3.upper() if code3 else None,
        "name": name,
        "official_name": _text(names.get("official")),
        "capitals": _capitals(record.get("capitals")),
        "region": _text(record.get("region")),
        "subregion": _text(record.get("subregion")),
        "languages": _languages(record.get("languages")),
        "currencies": _currencies(record.get("currencies")),
        "population": _population(record.get("population")),
        "flag": _text(_as_dict(record.get("flag")).get("url_png")),
    }


# --- Public functions ---


def normalize_countries(raw_records: list[dict]) -> dict[str, Country]:
    """Transform raw REST Countries v5 records into Country dicts keyed by alpha-2 code.

    Records without an alpha-2 code or a name are skipped. Missing values become None
    (single values) or empty lists (multi-value fields). The input is not modified.

    Args:
        raw_records: The ``records`` list returned by ``fetch_country_data()``.

    Returns:
        A dict such as ``{"JP": {...}, "CH": {...}}``.
    """
    countries: dict[str, Country] = {}
    for record in raw_records:
        if not isinstance(record, dict):
            continue
        country = _normalize_country(record)
        if country is not None:
            countries[country["code"]] = country
    return countries


# --- Phase 4: lookups for the screens (search, profile, compare) ---


def _country_for(code: str, countries: dict[str, Country]) -> Country:
    """Return the country for a code, or raise ValueError if the code is unknown."""
    if code not in countries:
        raise ValueError(f"Unknown country code: {code}")
    return countries[code]


def search_countries(
    countries: dict[str, Country], query: str = "", region: str | None = None
) -> list[Country]:
    """Filter countries by name and region, sorted alphabetically by name.

    Args:
        countries: The dict returned by ``normalize_countries()``.
        query: Text to look for anywhere in the name, ignoring case. Blank matches all.
        region: An exact region such as "Asia", or None for every region.

    Returns:
        Matching Country dicts sorted by name (ignoring case); ``[]`` if none match.
    """
    needle = query.strip().casefold()
    matches = [
        country
        for country in countries.values()
        if needle in country["name"].casefold() and (region is None or country["region"] == region)
    ]
    # casefold() is a stronger lower(): it makes the sort ignore capital letters.
    return sorted(matches, key=lambda country: country["name"].casefold())


def filter_phrases(phrases: list[dict], category: str | None = None) -> list[dict]:
    """Return the phrases in one category (CSV order kept), or all of them for None."""
    if category is None:
        return list(phrases)  # a new list, so the caller can't change the original
    return [phrase for phrase in phrases if phrase["category"] == category]


def build_country_profile(
    code: str,
    countries: dict[str, Country],
    phrases: list[dict],
    culture: list[dict],
    photos: list[dict],
) -> dict[str, Any]:
    """Combine one country's facts with its curated phrases, notes and photo.

    Uncurated countries get ``[]``, ``[]`` and ``None`` for the curated parts.

    Returns:
        {"country": Country, "phrases": [...], "culture": [...], "photo": row or None}.
        Phrases are ordered by PHRASE_CATEGORIES, then by their order in the CSV.

    Raises:
        ValueError: The code is not in ``countries``.
    """
    country = _country_for(code, countries)
    own_phrases = [phrase for phrase in phrases if phrase["country_code"] == code]
    # sorted() is stable, so phrases in the same category keep their CSV order.
    own_phrases = sorted(own_phrases, key=lambda phrase: _CATEGORY_RANK[phrase["category"]])
    # next(..., None) gives the first match, or None when there isn't one.
    photo = next((row for row in photos if row["country_code"] == code), None)
    return {
        "country": country,
        "phrases": own_phrases,
        "culture": [note for note in culture if note["country_code"] == code],
        "photo": photo,
    }


def build_population_series(
    countries: dict[str, Country], codes: list[str]
) -> list[dict[str, Any]]:
    """Data for the population bar chart, one entry per code, in ``codes`` order.

    A missing population stays None so the chart can show "Unavailable".

    Raises:
        ValueError: A code is not in ``countries``.
    """
    series = []
    for code in codes:
        country = _country_for(code, countries)
        series.append(
            {
                "code": country["code"],
                "code3": country["code3"],
                "name": country["name"],
                "population": country["population"],
            }
        )
    return series


def build_language_matrix(countries: dict[str, Country], codes: list[str]) -> dict[str, list]:
    """Data for the language matrix: which listed languages each country has.

    Columns: languages listed by the most countries first, ties and single-country
    languages alphabetical. Rows: one per code, in ``codes`` order, with one True/False
    mark per column.

    Returns:
        {"languages": ["French", ...], "rows": [{"code", "name", "marks": [bool, ...]}]}

    Raises:
        ValueError: A code is not in ``countries``.
    """
    selected = [_country_for(code, countries) for code in codes]
    # A set per country, so a language listed twice for one country counts once.
    language_sets = [{lang["name"] for lang in country["languages"]} for country in selected]

    counts: dict[str, int] = {}
    for names in language_sets:
        for name in names:
            counts[name] = counts.get(name, 0) + 1
    # Sorting by -count puts the most shared first; every unshared language has
    # count 1, so they end up last and alphabetical.
    languages = sorted(counts, key=lambda name: (-counts[name], name.casefold()))

    rows = [
        {
            "code": country["code"],
            "name": country["name"],
            "marks": [name in names for name in languages],
        }
        for country, names in zip(selected, language_sets, strict=True)
    ]
    return {"languages": languages, "rows": rows}


# --- Phase 5: small lookups the screens need ---


def list_regions(countries: dict[str, Country]) -> list[str]:
    """Every region that at least one country has, sorted A to Z (for the Region filter)."""
    regions = {country["region"] for country in countries.values() if country["region"]}
    return sorted(regions, key=str.casefold)


def curated_country_codes(phrases: list[dict]) -> set[str]:
    """Codes of the countries that have curated phrases (they get the Phrases badge)."""
    return {phrase["country_code"] for phrase in phrases}


def group_phrases(phrases: list[dict]) -> list[tuple[str, list[dict]]]:
    """Group phrases by category, in PHRASE_CATEGORIES order, skipping empty categories.

    Returns:
        A list such as [("greetings", [...]), ("basics", [...])]. Phrases keep their
        order within each group. The categories in the result are also the filter chips.
    """
    groups: dict[str, list[dict]] = {category: [] for category in PHRASE_CATEGORIES}
    for phrase in phrases:
        groups[phrase["category"]].append(phrase)
    return [(category, items) for category, items in groups.items() if items]


def bar_fractions(series: list[dict[str, Any]]) -> list[float | None]:
    """Each country's bar height as a share of the largest population (0.0 to 1.0).

    Used to draw the population bar chart: the tallest bar is 1.0 and the others are
    scaled to it. A missing population stays None so the chart can say "Unavailable".

    Args:
        series: The list returned by ``build_population_series()``.

    Returns:
        One value per entry, in the same order; all None if no population is known.
    """
    known = [entry["population"] for entry in series if entry["population"] is not None]
    largest = max(known, default=0)
    return [
        None if entry["population"] is None else (entry["population"] / largest if largest else 0.0)
        for entry in series
    ]
