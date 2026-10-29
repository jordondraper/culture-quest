"""Data access for country facts: the REST Countries API plus a short-lived cache.

fetch_country_data() never raises for expected problems (no key, no network, bad key,
rate limit, odd response, broken cache). It always returns a result dict, and the UI
decides what to show from its "source" and "error" keys.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from src.constants import (
    API_KEY_ENV_VAR,
    API_PROVIDER,
    API_URL,
    CACHE_MAX_AGE,
    DEFAULT_CACHE_PATH,
    ERROR_AUTH_FAILED,
    ERROR_BAD_RESPONSE,
    ERROR_NETWORK,
    ERROR_NO_API_KEY,
    ERROR_RATE_LIMITED,
    MAX_PAGES,
    PAGE_LIMIT,
    REQUEST_TIMEOUT_SECONDS,
    SOURCE_CACHE,
    SOURCE_LIVE,
    SOURCE_NONE,
)


class _FetchError(Exception):
    """Internal signal that the live fetch failed, carrying one of the error codes.

    It is raised deep inside the page loop and always caught in fetch_country_data(),
    so it never reaches the caller.
    """

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


# --- Public function ---


def fetch_country_data(cache_path: Path = DEFAULT_CACHE_PATH) -> dict[str, Any]:
    """Get raw country records, live from the API or from a cache no older than 3 days.

    Reads the API key from the REST_COUNTRIES_API_KEY environment variable (main.py loads
    .env first). On success, saves the records to the cache. On failure, falls back to a
    fresh cache; expired or corrupted cache files are deleted.

    Args:
        cache_path: Where the cache file lives. Tests pass a path inside tmp_path.

    Returns:
        {"records": list, "source": "live" | "cache" | "none",
         "fetched_at": UTC ISO string or None, "error": error code or None}
    """
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()

    if not api_key:
        error = ERROR_NO_API_KEY
    else:
        try:
            records = _fetch_all_pages(api_key)
        except _FetchError as exc:
            error = exc.code
        except requests.RequestException:  # connection refused, DNS failure, timeout...
            error = ERROR_NETWORK
        else:  # runs only when the try block raised nothing
            fetched_at = _utc_now_iso()
            _write_cache(cache_path, records, fetched_at)
            return _result(records, SOURCE_LIVE, fetched_at, None)

    cached = _read_fresh_cache(cache_path)
    if cached is not None:
        records, fetched_at = cached
        return _result(records, SOURCE_CACHE, fetched_at, error)
    return _result([], SOURCE_NONE, None, error)


# --- Live API ---


def _fetch_all_pages(api_key: str) -> list[dict]:
    """Request every page. All pages or nothing: any failure raises _FetchError."""
    records: list[dict] = []
    offset = 0
    for _ in range(MAX_PAGES):
        objects, more = _fetch_page(api_key, offset)
        records.extend(objects)
        if not more:
            if not records:
                raise _FetchError(ERROR_BAD_RESPONSE)  # a "successful" empty list is not usable
            return records
        if not objects:
            raise _FetchError(ERROR_BAD_RESPONSE)  # says "more" but sent nothing: avoid looping
        offset += len(objects)
    raise _FetchError(ERROR_BAD_RESPONSE)  # far more pages than expected


def _fetch_page(api_key: str, offset: int) -> tuple[list[dict], bool]:
    """Request one page and return (records, more). Raises _FetchError on bad status or shape."""
    response = requests.get(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        params={"limit": PAGE_LIMIT, "offset": offset},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code in (401, 403):
        raise _FetchError(ERROR_AUTH_FAILED)
    if response.status_code == 429:
        raise _FetchError(ERROR_RATE_LIMITED)
    if response.status_code != 200:
        raise _FetchError(ERROR_BAD_RESPONSE)

    try:
        body = response.json()
    except ValueError as exc:  # requests' JSON error is a subclass of ValueError
        raise _FetchError(ERROR_BAD_RESPONSE) from exc

    # Expected shape: {"data": {"objects": [...], "meta": {"more": bool, ...}}}
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        raise _FetchError(ERROR_BAD_RESPONSE)
    objects = data.get("objects")
    meta = data.get("meta")
    if not isinstance(objects, list) or not isinstance(meta, dict):
        raise _FetchError(ERROR_BAD_RESPONSE)
    return objects, bool(meta.get("more"))


# --- Cache ---


def _write_cache(cache_path: Path, records: list[dict], fetched_at: str) -> None:
    """Save records to the cache. A failed write never fails the fetch."""
    payload = {"fetched_at": fetched_at, "provider": API_PROVIDER, "records": records}
    temp_path = cache_path.with_suffix(".tmp")
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temporary file, then swap it in, so a crash mid-write can't leave
        # a half-written cache behind.
        temp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(cache_path)
    except OSError:
        pass  # live data is still returned; the next successful fetch tries again


def _read_fresh_cache(cache_path: Path) -> tuple[list[dict], str] | None:
    """Return (records, fetched_at) from a valid cache under 3 days old, else None.

    Corrupted and expired files are deleted (REST Countries terms forbid keeping
    data longer than 3 days).
    """
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        records = payload["records"]
        fetched_at = payload["fetched_at"]
        fetched_time = datetime.fromisoformat(fetched_at)
        if not isinstance(records, list) or fetched_time.tzinfo is None:
            raise ValueError("cache has the wrong shape")
    except (OSError, ValueError, KeyError, TypeError):
        # ValueError covers bad JSON, bad text encoding and bad timestamps.
        _delete(cache_path)
        return None

    if datetime.now(UTC) - fetched_time > CACHE_MAX_AGE:
        _delete(cache_path)
        return None
    return records, fetched_at


def _delete(path: Path) -> None:
    """Delete a file if possible; a file we can't delete is not worth crashing over."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


# --- Small helpers ---


def _utc_now_iso() -> str:
    """Current UTC time as an ISO string, e.g. "2026-10-29T07:15:00Z"."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _result(records: list, source: str, fetched_at: str | None, error: str | None) -> dict:
    """Build the result dict so every return has exactly the same four keys."""
    return {"records": records, "source": source, "fetched_at": fetched_at, "error": error}
