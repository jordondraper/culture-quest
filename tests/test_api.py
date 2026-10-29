"""Tests for src/api.py.

No test touches the real network or the real data/cache folder:
- requests.get is replaced by a fake API built from the hand-written fixture records.
- every test passes a cache path inside pytest's tmp_path folder.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest
import requests

from src import api
from src.constants import (
    API_KEY_ENV_VAR,
    ERROR_AUTH_FAILED,
    ERROR_BAD_RESPONSE,
    ERROR_NETWORK,
    ERROR_NO_API_KEY,
    ERROR_RATE_LIMITED,
)

# --- Test helpers ---


class FakeResponse:
    """Just enough of requests.Response for api.py: status_code and json()."""

    def __init__(self, status_code=200, body=None, invalid_json=False):
        self.status_code = status_code
        self._body = body
        self._invalid_json = invalid_json

    def json(self):
        if self._invalid_json:
            raise requests.JSONDecodeError("Expecting value", "", 0)
        return self._body


def page_body(objects, more):
    """A response body shaped like REST Countries v5."""
    return {"data": {"objects": objects, "meta": {"count": len(objects), "more": more}}}


class FakeApi:
    """Stands in for requests.get: serves records in pages and remembers each call."""

    def __init__(self, records, fail_on_call=None, failure=None):
        self.records = records
        self.calls = []
        self.fail_on_call = fail_on_call  # 1-based call number that should fail
        self.failure = failure  # a FakeResponse to return, or an exception to raise

    def __call__(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        if len(self.calls) == self.fail_on_call:
            if isinstance(self.failure, Exception):
                raise self.failure
            return self.failure
        offset, limit = params["offset"], params["limit"]
        page = self.records[offset : offset + limit]
        return FakeResponse(200, page_body(page, more=offset + limit < len(self.records)))


def write_cache(path, records, age):
    """Write a cache file whose fetched_at is `age` ago."""
    fetched_at = (datetime.now(UTC) - age).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": fetched_at, "provider": "test", "records": records}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return fetched_at


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    """Runs before every test: any real request fails loudly instead of using the quota."""

    def refuse(*args, **kwargs):
        raise AssertionError("A test tried to call the real API")

    monkeypatch.setattr(api.requests, "get", refuse)


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "test-key")


@pytest.fixture
def small_pages(monkeypatch):
    """Two records per page, so the five fixture records need three requests."""
    monkeypatch.setattr(api, "PAGE_LIMIT", 2)


@pytest.fixture
def cache_path(tmp_path):
    return tmp_path / "cache" / "countries.json"


def use_fake_api(monkeypatch, fake):
    monkeypatch.setattr(api.requests, "get", fake)
    return fake


# --- Live success ---


def test_live_success_returns_all_records(
    monkeypatch, api_key, small_pages, raw_records, cache_path
):
    fake = use_fake_api(monkeypatch, FakeApi(raw_records))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result["source"] == "live"
    assert result["error"] is None
    assert result["records"] == raw_records
    assert result["fetched_at"].endswith("Z")
    assert [call["params"]["offset"] for call in fake.calls] == [0, 2, 4]


def test_requests_use_bearer_key_and_timeout(monkeypatch, api_key, raw_records, cache_path):
    fake = use_fake_api(monkeypatch, FakeApi(raw_records))

    api.fetch_country_data(cache_path=cache_path)

    assert fake.calls[0]["headers"] == {"Authorization": "Bearer test-key"}
    assert fake.calls[0]["timeout"] is not None


def test_live_success_writes_cache_and_creates_folder(monkeypatch, api_key, raw_records, tmp_path):
    use_fake_api(monkeypatch, FakeApi(raw_records))
    cache_path = tmp_path / "not" / "created" / "yet" / "countries.json"

    result = api.fetch_country_data(cache_path=cache_path)

    saved = json.loads(cache_path.read_text(encoding="utf-8"))
    assert saved["records"] == raw_records
    assert saved["fetched_at"] == result["fetched_at"]
    assert "provider" in saved


def test_live_success_replaces_older_cache(monkeypatch, api_key, raw_records, cache_path):
    write_cache(cache_path, [{"old": True}], age=timedelta(days=1))
    use_fake_api(monkeypatch, FakeApi(raw_records))

    api.fetch_country_data(cache_path=cache_path)

    assert json.loads(cache_path.read_text(encoding="utf-8"))["records"] == raw_records


def test_failed_cache_write_still_returns_live_data(monkeypatch, api_key, raw_records, tmp_path):
    use_fake_api(monkeypatch, FakeApi(raw_records))
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, so no folder can be created here")

    result = api.fetch_country_data(cache_path=blocker / "countries.json")

    assert result["source"] == "live"
    assert result["records"] == raw_records


# --- Failures map to error codes (no cache available) ---


@pytest.mark.parametrize(
    ("failure", "expected_error"),
    [
        (FakeResponse(401), ERROR_AUTH_FAILED),
        (FakeResponse(403), ERROR_AUTH_FAILED),
        (FakeResponse(429), ERROR_RATE_LIMITED),
        (FakeResponse(500), ERROR_BAD_RESPONSE),
        (FakeResponse(200, invalid_json=True), ERROR_BAD_RESPONSE),
        (FakeResponse(200, body={"unexpected": "shape"}), ERROR_BAD_RESPONSE),
        (FakeResponse(200, body=["not", "a", "dict"]), ERROR_BAD_RESPONSE),
        (requests.ConnectionError("no connection"), ERROR_NETWORK),
        (requests.Timeout("too slow"), ERROR_NETWORK),
    ],
)
def test_failure_without_cache_returns_none(
    monkeypatch, api_key, raw_records, cache_path, failure, expected_error
):
    use_fake_api(monkeypatch, FakeApi(raw_records, fail_on_call=1, failure=failure))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result == {"records": [], "source": "none", "fetched_at": None, "error": expected_error}


def test_failure_on_a_later_page_fails_the_whole_fetch(
    monkeypatch, api_key, small_pages, raw_records, cache_path
):
    failure = FakeResponse(429)
    use_fake_api(monkeypatch, FakeApi(raw_records, fail_on_call=2, failure=failure))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result["source"] == "none"
    assert result["records"] == []
    assert not cache_path.exists()  # partial data is never saved


def test_empty_live_result_is_a_bad_response(monkeypatch, api_key, cache_path):
    use_fake_api(monkeypatch, FakeApi([]))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result["error"] == ERROR_BAD_RESPONSE


def test_page_claiming_more_but_empty_stops(monkeypatch, api_key, cache_path):
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: FakeResponse(200, page_body([], True)))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result["error"] == ERROR_BAD_RESPONSE


# --- Failures fall back to the cache ---


def test_failure_with_fresh_cache_returns_cached_data(
    monkeypatch, api_key, raw_records, cache_path
):
    fetched_at = write_cache(cache_path, raw_records, age=timedelta(days=1))
    use_fake_api(monkeypatch, FakeApi([], fail_on_call=1, failure=requests.ConnectionError()))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result == {
        "records": raw_records,
        "source": "cache",
        "fetched_at": fetched_at,
        "error": ERROR_NETWORK,
    }


def test_failure_with_expired_cache_deletes_it(monkeypatch, api_key, raw_records, cache_path):
    write_cache(cache_path, raw_records, age=timedelta(days=5))
    use_fake_api(monkeypatch, FakeApi([], fail_on_call=1, failure=requests.ConnectionError()))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result["source"] == "none"
    assert result["error"] == ERROR_NETWORK
    assert not cache_path.exists()


@pytest.mark.parametrize(
    "bad_content",
    [
        "{ not valid json",
        json.dumps({"records": []}),  # no fetched_at
        json.dumps({"fetched_at": "2026-10-28T00:00:00Z"}),  # no records
        json.dumps({"fetched_at": "not a date", "records": []}),
        json.dumps({"fetched_at": "2026-10-28T00:00:00", "records": []}),  # no time zone
        json.dumps({"fetched_at": "2026-10-28T00:00:00Z", "records": "not a list"}),
        json.dumps(["not", "a", "dict"]),
    ],
)
def test_corrupted_cache_is_deleted(monkeypatch, api_key, cache_path, bad_content):
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(bad_content, encoding="utf-8")
    use_fake_api(monkeypatch, FakeApi([], fail_on_call=1, failure=requests.ConnectionError()))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result["source"] == "none"
    assert not cache_path.exists()


# --- No API key ---


@pytest.mark.parametrize("key_value", [None, "", "   "])
def test_no_api_key_skips_network(monkeypatch, cache_path, key_value):
    if key_value is None:
        monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(API_KEY_ENV_VAR, key_value)
    # no_real_network is still active: any request would fail this test

    result = api.fetch_country_data(cache_path=cache_path)

    assert result == {
        "records": [],
        "source": "none",
        "fetched_at": None,
        "error": ERROR_NO_API_KEY,
    }


def test_no_api_key_uses_fresh_cache(monkeypatch, raw_records, cache_path):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    fetched_at = write_cache(cache_path, raw_records, age=timedelta(hours=2))

    result = api.fetch_country_data(cache_path=cache_path)

    assert result["source"] == "cache"
    assert result["records"] == raw_records
    assert result["fetched_at"] == fetched_at
    assert result["error"] == ERROR_NO_API_KEY
