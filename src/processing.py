"""Pure data transformations for CultureQuest.

Nothing in this module touches the network, files, or the UI, so every function can be
tested with plain Python data.
"""

from typing import Any

Country = dict[str, Any]


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
