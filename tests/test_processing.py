"""Tests for src/processing.py."""

import copy

import pytest

from src.processing import normalize_countries

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
