"""Tests for src/state.py."""

import pytest

from src.state import AppState


def _make_loader(codes, source="live"):
    """A fake loader returning one minimal country per code; no files or network."""

    def loader():
        return {
            "countries": {code: {"code": code, "name": code} for code in codes},
            "phrases": [{"country_code": codes[0]}] if codes else [],
            "culture": [],
            "photos": [],
            "source": source,
            "fetched_at": "2026-10-29T08:00:00+00:00",
            "fetch_error": None,
            "content_error": None,
        }

    return loader


@pytest.fixture
def state():
    """A loaded AppState with six countries, one more than the compare limit."""
    app_state = AppState(loader=_make_loader(["BR", "CH", "FR", "JP", "KR", "MX"]))
    app_state.reload()
    return app_state


# --- Defaults ---


def test_new_state_is_empty_until_reload():
    app_state = AppState(loader=_make_loader(["JP"]))
    assert app_state.countries == {}
    assert app_state.source == "none"
    assert app_state.search_query == ""
    assert app_state.region_filter is None
    assert app_state.compare_codes == []


def test_states_do_not_share_lists():
    first = AppState(loader=_make_loader(["JP"]))
    second = AppState(loader=_make_loader(["JP"]))
    first.compare_codes.append("JP")
    assert second.compare_codes == []


# --- reload() ---


def test_reload_replaces_all_loaded_data(state):
    state.loader = _make_loader(["JP", "MX"], source="cache")
    state.reload()
    assert set(state.countries) == {"JP", "MX"}
    assert state.phrases == [{"country_code": "JP"}]
    assert state.source == "cache"


def test_reload_keeps_selections(state):
    state.search_query = "ja"
    state.region_filter = "Asia"
    state.add_to_compare("JP")
    state.reload()
    assert (state.search_query, state.region_filter) == ("ja", "Asia")
    assert state.compare_codes == ["JP"]


def test_reload_drops_compare_codes_that_no_longer_exist(state):
    for code in ["JP", "FR", "MX"]:
        state.add_to_compare(code)
    state.loader = _make_loader(["JP", "MX"])
    state.reload()
    assert state.compare_codes == ["JP", "MX"]


def test_reload_failure_keeps_old_data(state):
    def broken_loader():
        raise RuntimeError("boom")

    state.loader = broken_loader
    with pytest.raises(RuntimeError):
        state.reload()
    assert "BR" in state.countries


# --- Compare list ---


def test_add_to_compare_accepts_up_to_five(state):
    for code in ["BR", "CH", "FR", "JP", "KR"]:
        assert state.add_to_compare(code) is True
    assert state.add_to_compare("MX") is False
    assert state.compare_codes == ["BR", "CH", "FR", "JP", "KR"]


def test_add_to_compare_rejects_duplicate(state):
    assert state.add_to_compare("JP") is True
    assert state.add_to_compare("JP") is False
    assert state.compare_codes == ["JP"]


def test_add_to_compare_rejects_unknown_code(state):
    assert state.add_to_compare("XX") is False
    assert state.compare_codes == []


def test_remove_from_compare(state):
    state.add_to_compare("JP")
    state.add_to_compare("FR")
    state.remove_from_compare("JP")
    assert state.compare_codes == ["FR"]


def test_remove_absent_code_does_nothing(state):
    state.add_to_compare("JP")
    state.remove_from_compare("MX")
    assert state.compare_codes == ["JP"]


@pytest.mark.parametrize(("count", "expected"), [(0, False), (1, False), (2, True), (5, True)])
def test_can_compare_needs_two_to_five(state, count, expected):
    for code in ["BR", "CH", "FR", "JP", "KR"][:count]:
        state.add_to_compare(code)
    assert state.can_compare() is expected
