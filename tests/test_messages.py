"""Tests for ui/messages.py: the exact wording and formatting the user sees."""

import pytest

from ui import messages

# --- population_text() ---


@pytest.mark.parametrize(
    ("population", "expected"),
    [
        (None, "Unavailable"),
        (1_438_000_000, "About 1.4 billion"),
        (2_000_000_000, "About 2 billion"),
        (123_975_000, "About 124 million"),
        (68_170_000, "About 68 million"),
        (8_740_000, "About 8.7 million"),
        (1_000_000, "About 1 million"),
        (38_750, "About 39,000"),
        (1_000, "1,000"),
        (0, "0"),
    ],
)
def test_population_text(population, expected):
    assert messages.population_text(population) == expected


# --- Dates ---


def test_date_text_formats_a_utc_timestamp():
    # Midday UTC is the same calendar day in every time zone the app is likely used in.
    assert messages.date_text("2026-10-28T12:00:00Z") == "Oct 28, 2026"


def test_date_text_has_no_leading_zero():
    assert messages.date_text("2026-11-05T12:00:00Z") == "Nov 5, 2026"


@pytest.mark.parametrize("value", [None, "", "yesterday"])
def test_date_text_missing_or_bad_is_unavailable(value):
    assert messages.date_text(value) == "Unavailable"


def test_reviewed_text():
    assert messages.reviewed_text("2026-10-29") == "Reviewed Oct 2026"


def test_reviewed_text_bad_date_is_blank():
    assert messages.reviewed_text("Oct 2026") == ""


# --- Status ---


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("network", "Check your internet connection."),
        ("no_api_key", "The REST Countries API key is missing. Add it to the .env file."),
        ("auth_failed", "The REST Countries API key wasn't accepted. Check the .env file."),
        ("rate_limited", "The REST Countries request limit was reached. Try again later."),
        ("bad_response", "REST Countries sent an unexpected response. Try again later."),
        (None, "Something went wrong. Try again."),
        ("surprise", "Something went wrong. Try again."),
    ],
)
def test_error_reason(code, expected):
    assert messages.error_reason(code) == expected


def test_offline_banner_text():
    text = messages.offline_banner_text("2026-10-28T12:00:00Z")
    assert text == "Showing saved data from Oct 28, 2026."


@pytest.mark.parametrize(
    ("source", "expected"),
    [("live", "Live from REST Countries"), ("cache", "Saved data"), ("none", "Unavailable")],
)
def test_source_text(source, expected):
    assert messages.source_text(source) == expected


# --- Explore ---


@pytest.mark.parametrize(
    ("count", "expected"), [(0, "0 countries"), (1, "1 country"), (4, "4 countries")]
)
def test_result_count(count, expected):
    assert messages.result_count(count) == expected


def test_no_results_quotes_the_trimmed_query():
    assert messages.no_results("  Atlantis ") == "No countries match “Atlantis”."


def test_tile_subtitle(countries):
    assert messages.tile_subtitle(countries["JP"]) == "Asia · Tokyo"


def test_tile_subtitle_skips_missing_parts(countries):
    countries["JP"]["capitals"] = []
    assert messages.tile_subtitle(countries["JP"]) == "Asia"
    countries["JP"]["region"] = None
    assert messages.tile_subtitle(countries["JP"]) == ""


# --- Profile ---


def test_region_line(countries):
    assert messages.region_line(countries["JP"]) == "Asia · Eastern Asia"


def test_official_name_only_when_different(countries):
    assert messages.official_name_line(countries["JP"]) is None
    countries["JP"]["official_name"] = "State of Japan"
    assert messages.official_name_line(countries["JP"]) == "State of Japan"
    countries["JP"]["official_name"] = None
    assert messages.official_name_line(countries["JP"]) is None


def test_capital_text():
    assert messages.capital_text(["Pretoria", "Cape Town"]) == "Pretoria, Cape Town"
    assert messages.capital_text([]) == "Unavailable"


def test_languages_label_and_text():
    one = [{"code": "jpn", "name": "Japanese"}]
    two = one + [{"code": "ain", "name": "Ainu"}]
    assert messages.languages_label(one) == "Language"
    assert messages.languages_label(two) == "Languages"
    assert messages.languages_text(two) == "Japanese, Ainu"
    assert messages.languages_text([]) == "Unavailable"


def test_currency_text():
    yen = {"code": "JPY", "name": "Japanese yen", "symbol": "¥"}
    no_symbol = {"code": "XYZ", "name": "Test dollar", "symbol": None}
    assert messages.currency_text([yen]) == "Japanese yen (¥)"
    assert messages.currency_text([yen, no_symbol]) == "Japanese yen (¥), Test dollar"
    assert messages.currency_text([]) == "Unavailable"


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("greetings", "Greetings"),
        ("basics", "Basics"),
        ("dining", "Dining"),
        ("getting_around", "Getting around"),
        ("shopping", "Shopping"),
        ("emergencies", "Emergencies"),
    ],
)
def test_category_label(category, expected):
    assert messages.category_label(category) == expected


def test_phrase_source_text():
    expected = "Source: Wikivoyage Japanese phrasebook · CC BY-SA"
    assert messages.phrase_source_text("Japanese") == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.japan.travel/en/responsible-travel-guide/", "JNTO"),
        ("https://ich.unesco.org/en/RL/00869", "UNESCO"),
        ("https://en.wikivoyage.org/wiki/Japanese_phrasebook", "Wikivoyage"),
        ("https://www.visitexample.test/culture", "visitexample.test"),
    ],
)
def test_source_name(url, expected):
    assert messages.source_name(url) == expected


def test_photo_credit(content):
    expected = "Photo: Test Photographer · CC BY-SA 4.0 · Wikimedia Commons"
    assert messages.photo_credit(content["photos"][0]) == expected


def test_compare_full_hint_uses_the_limit():
    assert messages.COMPARE_FULL_HINT == "Maximum of 5. Remove one in Compare to add another."


def test_remove_label():
    assert messages.remove_label("Japan") == "Remove Japan"
