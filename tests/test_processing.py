"""Tests for src/processing.py."""

import copy

import pytest

from src.processing import (
    build_country_profile,
    build_language_matrix,
    build_population_series,
    filter_phrases,
    normalize_countries,
    search_countries,
)

CONTRACT_KEYS = {
    "code",
    "code3",
    "name",
    "official_name",
    "capitals",
    "region",
    "subregion",
    "languages",
    "currencies",
    "population",
    "flag",
}

# --- normalize_countries() ---


def test_returns_countries_keyed_by_alpha2_code(raw_records):
    countries = normalize_countries(raw_records)
    assert set(countries) == {"JP", "ZA", "CH", "AQ"}


def test_record_without_alpha2_code_is_skipped(raw_records):
    countries = normalize_countries(raw_records)
    assert all(country["name"] != "Testland" for country in countries.values())


def test_every_country_has_exactly_the_contract_keys(raw_records):
    for country in normalize_countries(raw_records).values():
        assert set(country) == CONTRACT_KEYS


def test_baseline_country_fields(raw_records):
    japan = normalize_countries(raw_records)["JP"]
    assert japan["code3"] == "JPN"
    assert japan["name"] == "Japan"
    assert japan["official_name"] == "Japan"
    assert japan["region"] == "Asia"
    assert japan["subregion"] == "Eastern Asia"
    assert japan["population"] == 123000000
    assert japan["flag"] == "https://flags.example.test/w640/jp.png"


def test_single_capital(raw_records):
    assert normalize_countries(raw_records)["JP"]["capitals"] == ["Tokyo"]


def test_multiple_capitals_keep_all_with_primary_first(raw_records):
    capitals = normalize_countries(raw_records)["ZA"]["capitals"]
    assert capitals == ["Pretoria", "Bloemfontein", "Cape Town"]


def test_single_language(raw_records):
    assert normalize_countries(raw_records)["JP"]["languages"] == [
        {"code": "jpn", "name": "Japanese"}
    ]


def test_multiple_languages_keep_api_order(raw_records):
    languages = normalize_countries(raw_records)["CH"]["languages"]
    assert [language["name"] for language in languages] == [
        "German",
        "French",
        "Italian",
        "Romansh",
    ]


def test_currencies_keep_code_name_and_symbol(raw_records):
    assert normalize_countries(raw_records)["JP"]["currencies"] == [
        {"code": "JPY", "name": "Japanese yen", "symbol": "¥"}
    ]


def test_missing_fields_become_none_or_empty_lists(raw_records):
    antarctica = normalize_countries(raw_records)["AQ"]
    assert antarctica["capitals"] == []
    assert antarctica["languages"] == []
    assert antarctica["currencies"] == []
    assert antarctica["subregion"] is None  # API sent ""
    assert antarctica["flag"] is None  # API sent ""
    assert antarctica["population"] is None


def test_codes_are_uppercased_and_trimmed(raw_records):
    raw_records[0]["codes"] = {"alpha_2": " jp ", "alpha_3": "jpn"}
    japan = normalize_countries(raw_records)["JP"]
    assert japan["code"] == "JP"
    assert japan["code3"] == "JPN"


def test_text_is_trimmed(raw_records):
    raw_records[0]["names"]["common"] = "  Japan  "
    assert normalize_countries(raw_records)["JP"]["name"] == "Japan"


@pytest.mark.parametrize("bad_value", [None, "", "125", -5, True, 3.5])
def test_invalid_population_becomes_none(raw_records, bad_value):
    raw_records[0]["population"] = bad_value
    assert normalize_countries(raw_records)["JP"]["population"] is None


def test_currency_without_symbol_keeps_symbol_as_none(raw_records):
    raw_records[0]["currencies"] = [{"code": "JPY", "name": "Japanese yen", "symbol": ""}]
    currency = normalize_countries(raw_records)["JP"]["currencies"][0]
    assert currency["symbol"] is None


def test_empty_input_returns_empty_dict():
    assert normalize_countries([]) == {}


def test_input_is_not_modified(raw_records):
    before = copy.deepcopy(raw_records)
    normalize_countries(raw_records)
    assert raw_records == before


# --- Phase 4 helpers ---


def _names(country_list):
    return [country["name"] for country in country_list]


def _country(code, name, languages):
    """A minimal Country for the language-matrix tests."""
    return {
        "code": code,
        "code3": None,
        "name": name,
        "languages": [{"code": None, "name": language} for language in languages],
    }


def _phrase(category, english, code="JP"):
    return {"country_code": code, "category": category, "english": english}


# --- search_countries() ---


def test_search_blank_query_returns_all_sorted_by_name(countries):
    assert _names(search_countries(countries)) == [
        "Antarctica",
        "Japan",
        "South Africa",
        "Switzerland",
    ]


def test_search_ignores_case_and_matches_inside_the_name(countries):
    assert _names(search_countries(countries, "AFR")) == ["South Africa"]


def test_search_ignores_surrounding_spaces(countries):
    assert _names(search_countries(countries, "  japan ")) == ["Japan"]


def test_search_filters_by_exact_region(countries):
    assert _names(search_countries(countries, region="Europe")) == ["Switzerland"]


def test_search_combines_query_and_region(countries):
    assert search_countries(countries, "japan", region="Europe") == []


def test_search_with_no_match_returns_empty_list(countries):
    assert search_countries(countries, "zzz") == []


def test_search_sort_ignores_case():
    countries = {
        "AA": {"name": "bravo", "region": None},
        "BB": {"name": "Alpha", "region": None},
    }
    assert _names(search_countries(countries)) == ["Alpha", "bravo"]


# --- filter_phrases() ---


def test_filter_phrases_none_returns_all_in_order(content):
    phrases = content["phrases"]
    assert filter_phrases(phrases) == phrases


def test_filter_phrases_by_category_keeps_order(content):
    result = filter_phrases(content["phrases"], "greetings")
    assert [(p["country_code"], p["english"]) for p in result] == [
        ("JP", "Hello"),
        ("FR", "Hello"),
    ]


def test_filter_phrases_unused_category_returns_empty_list(content):
    assert filter_phrases(content["phrases"], "emergencies") == []


def test_filter_phrases_returns_a_new_list(content):
    phrases = content["phrases"]
    filter_phrases(phrases).clear()
    assert len(phrases) == 3


# --- build_country_profile() ---


def test_profile_of_curated_country(countries, content):
    profile = build_country_profile("JP", countries, **content)
    assert profile["country"]["name"] == "Japan"
    assert [p["english"] for p in profile["phrases"]] == ["Hello", "The check, please"]
    assert [n["topic"] for n in profile["culture"]] == ["Shoes off indoors", "Hot springs"]
    assert profile["photo"]["photographer"] == "Test Photographer"


def test_profile_of_uncurated_country_has_empty_content(countries, content):
    profile = build_country_profile("CH", countries, **content)
    assert profile["country"]["name"] == "Switzerland"
    assert profile["phrases"] == []
    assert profile["culture"] == []
    assert profile["photo"] is None


def test_profile_phrases_follow_category_order_then_csv_order(countries):
    phrases = [
        _phrase("dining", "Water"),
        _phrase("greetings", "Hello"),
        _phrase("dining", "The check"),
        _phrase("basics", "Thank you"),
        _phrase("greetings", "Hello", code="FR"),
    ]
    profile = build_country_profile("JP", countries, phrases, [], [])
    assert [p["english"] for p in profile["phrases"]] == [
        "Hello",
        "Thank you",
        "Water",
        "The check",
    ]


def test_profile_unknown_code_raises(countries, content):
    with pytest.raises(ValueError, match="Unknown country code: XX"):
        build_country_profile("XX", countries, **content)


def test_profile_does_not_modify_inputs(countries, content):
    before = copy.deepcopy((countries, content))
    build_country_profile("JP", countries, **content)
    assert (countries, content) == before


# --- build_population_series() ---


def test_population_series_follows_codes_order(countries):
    series = build_population_series(countries, ["CH", "JP"])
    assert series == [
        {"code": "CH", "code3": "CHE", "name": "Switzerland", "population": 8_700_000},
        {"code": "JP", "code3": "JPN", "name": "Japan", "population": 123_000_000},
    ]


def test_population_series_keeps_missing_population_as_none(countries):
    series = build_population_series(countries, ["AQ", "JP"])
    assert series[0]["population"] is None


def test_population_series_empty_codes_returns_empty_list(countries):
    assert build_population_series(countries, []) == []


def test_population_series_unknown_code_raises(countries):
    with pytest.raises(ValueError, match="Unknown country code: XX"):
        build_population_series(countries, ["JP", "XX"])


# --- build_language_matrix() ---


def test_language_matrix_shared_languages_first_then_alphabetical():
    countries = {
        "FR": _country("FR", "France", ["French"]),
        "CH": _country("CH", "Switzerland", ["German", "French", "Italian", "Romansh"]),
        "CA": _country("CA", "Canada", ["English", "French"]),
        "BR": _country("BR", "Brazil", ["Portuguese"]),
    }
    matrix = build_language_matrix(countries, ["FR", "CH", "CA", "BR"])
    assert matrix["languages"] == [
        "French",
        "English",
        "German",
        "Italian",
        "Portuguese",
        "Romansh",
    ]
    assert matrix["rows"][2] == {
        "code": "CA",
        "name": "Canada",
        "marks": [True, True, False, False, False, False],
    }


def test_language_matrix_most_shared_language_leads():
    countries = {
        "A": _country("A", "A", ["Zulu", "English"]),
        "B": _country("B", "B", ["Zulu", "English"]),
        "C": _country("C", "C", ["Zulu"]),
    }
    matrix = build_language_matrix(countries, ["A", "B", "C"])
    assert matrix["languages"] == ["Zulu", "English"]


def test_language_matrix_rows_follow_codes_order(countries):
    matrix = build_language_matrix(countries, ["ZA", "JP"])
    assert [row["code"] for row in matrix["rows"]] == ["ZA", "JP"]
    assert matrix["languages"] == ["English", "Japanese", "Zulu"]


def test_language_matrix_country_without_languages_has_all_false(countries):
    matrix = build_language_matrix(countries, ["JP", "AQ"])
    assert matrix["rows"][1]["marks"] == [False]


def test_language_matrix_counts_a_repeated_language_once():
    countries = {
        "A": _country("A", "A", ["French", "French"]),
        "B": _country("B", "B", ["English"]),
    }
    matrix = build_language_matrix(countries, ["A", "B"])
    assert matrix["languages"] == ["English", "French"]


def test_language_matrix_unknown_code_raises(countries):
    with pytest.raises(ValueError, match="Unknown country code: XX"):
        build_language_matrix(countries, ["XX"])


def test_compare_builders_do_not_modify_inputs(countries):
    before = copy.deepcopy(countries)
    build_population_series(countries, ["JP", "CH"])
    build_language_matrix(countries, ["JP", "CH"])
    assert countries == before
