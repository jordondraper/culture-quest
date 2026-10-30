"""Tests for src/loaders.py.

The valid files live in tests/fixtures/. Each invalid case copies a valid file into
pytest's tmp_path folder and changes one thing, so every test breaks exactly one rule.
"""

from pathlib import Path

import pytest

from src import loaders
from src.loaders import load_curated_content

FIXTURES_DIR = Path(__file__).parent / "fixtures"

PHRASES = FIXTURES_DIR / "phrases_valid.csv"
CULTURE = FIXTURES_DIR / "culture_valid.csv"
PHOTOS = FIXTURES_DIR / "photos_valid.csv"


def load(phrases=PHRASES, culture=CULTURE, photos=PHOTOS):
    return load_curated_content(phrase_path=phrases, culture_path=culture, photo_path=photos)


def broken_copy(tmp_path, source, old, new):
    """Copy a valid fixture into tmp_path with one piece of text replaced."""
    text = source.read_text(encoding="utf-8")
    assert old in text, f"test setup: {old!r} not found in {source.name}"
    path = tmp_path / source.name
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path


# --- Valid files ---


def test_valid_files_load_every_row():
    content = load()
    assert set(content) == {"phrases", "culture", "photos"}
    assert len(content["phrases"]) == 3
    assert len(content["culture"]) == 2
    assert len(content["photos"]) == 1


def test_rows_keep_unicode_and_quoted_commas():
    first, second, _ = load()["phrases"]
    assert first["native"] == "こんにちは"
    assert second["english"] == "The check, please"


def test_optional_columns_may_be_blank():
    content = load()
    assert content["phrases"][2]["romanization"] == ""  # French
    assert content["culture"][0]["community"] == ""


def test_values_are_trimmed_and_extra_columns_dropped(tmp_path):
    path = tmp_path / "phrases.csv"
    path.write_text(
        "country_code,category,english,native,romanization,language,source_url,reviewed_on,note\n"
        " JP ,greetings, Hello ,こんにちは,konnichiwa,Japanese,https://example.test/x,2026-10-29,x\n",
        encoding="utf-8",
    )
    row = load(phrases=path)["phrases"][0]
    assert row["country_code"] == "JP"
    assert row["english"] == "Hello"
    assert "note" not in row


def test_byte_order_mark_is_accepted(tmp_path):
    path = tmp_path / "phrases.csv"
    path.write_text(PHRASES.read_text(encoding="utf-8"), encoding="utf-8-sig")
    assert len(load(phrases=path)["phrases"]) == 3


def test_blank_lines_are_skipped(tmp_path):
    path = tmp_path / "phrases.csv"
    path.write_text(PHRASES.read_text(encoding="utf-8") + "\n,,,,,,,\n", encoding="utf-8")
    assert len(load(phrases=path)["phrases"]) == 3


# --- Invalid files: the message names the file, the row and the problem ---


def test_unknown_category(tmp_path):
    path = broken_copy(tmp_path, PHRASES, "JP,dining,", "JP,food,")
    with pytest.raises(ValueError, match=r'phrases_valid\.csv row 3: unknown category "food"'):
        load(phrases=path)


@pytest.mark.parametrize("bad_code", ["jp", "JPN", "J1", ""])
def test_invalid_country_code(tmp_path, bad_code):
    path = broken_copy(tmp_path, CULTURE, "JP,Hot springs", f"{bad_code},Hot springs")
    with pytest.raises(ValueError, match=r"culture_valid\.csv row 3: country_code"):
        load(culture=path)


def test_missing_column(tmp_path):
    path = broken_copy(tmp_path, CULTURE, ",reviewed_on", ",checked")
    with pytest.raises(ValueError, match=r"culture_valid\.csv: missing column\(s\) reviewed_on"):
        load(culture=path)


def test_required_value_is_empty(tmp_path):
    path = broken_copy(tmp_path, PHRASES, ",Bonjour,", ",,")
    with pytest.raises(ValueError, match=r"phrases_valid\.csv row 4: native is empty"):
        load(phrases=path)


def test_invalid_review_date(tmp_path):
    path = broken_copy(tmp_path, CULTURE, "2026-10-29", "29/10/2026")
    with pytest.raises(ValueError, match=r"culture_valid\.csv row 2: reviewed_on"):
        load(culture=path)


def test_source_url_must_be_https(tmp_path):
    path = broken_copy(tmp_path, PHOTOS, "https://example.test/file", "www.example.test/file")
    with pytest.raises(ValueError, match=r"photos_valid\.csv row 2: source_url"):
        load(photos=path)


def test_image_url_must_be_https(tmp_path):
    path = broken_copy(tmp_path, PHOTOS, "https://example.test/images", "http://example.test/i")
    with pytest.raises(ValueError, match=r"photos_valid\.csv row 2: image_url"):
        load(photos=path)


def test_duplicate_phrase(tmp_path):
    path = tmp_path / "phrases.csv"
    lines = PHRASES.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([*lines, lines[1]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"phrases\.csv row 5: duplicate of row 2"):
        load(phrases=path)


def test_second_photo_for_same_country(tmp_path):
    path = tmp_path / "photos.csv"
    lines = PHOTOS.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([*lines, lines[1]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"photos\.csv row 3: duplicate of row 2"):
        load(photos=path)


def test_missing_file(tmp_path):
    with pytest.raises(ValueError, match=r"culture\.csv: file not found"):
        load(culture=tmp_path / "culture.csv")


def test_file_not_saved_as_utf8(tmp_path):
    path = tmp_path / "phrases.csv"
    path.write_bytes(
        PHRASES.read_text(encoding="utf-8")
        .replace("こんにちは", "Olá")
        .encode("latin-1", "replace")
    )
    with pytest.raises(ValueError, match=r"phrases\.csv: not saved as UTF-8"):
        load(phrases=path)


# --- load_app_data() (fetch and CSV loading replaced with fakes) ---


def _fake_fetch(records, source="live", error=None):
    def fetch():
        fetched_at = None if source == "none" else "2026-10-28T15:00:00Z"
        return {"records": records, "source": source, "fetched_at": fetched_at, "error": error}

    return fetch


@pytest.fixture
def fake_content(monkeypatch, content):
    monkeypatch.setattr(loaders, "load_curated_content", lambda: content)
    return content


def test_load_app_data_combines_countries_and_content(monkeypatch, raw_records, fake_content):
    monkeypatch.setattr(loaders, "fetch_country_data", _fake_fetch(raw_records))
    data = loaders.load_app_data()
    assert set(data) == {
        "countries",
        "phrases",
        "culture",
        "photos",
        "source",
        "fetched_at",
        "fetch_error",
        "content_error",
    }
    assert set(data["countries"]) == {"JP", "ZA", "CH", "AQ"}
    assert data["phrases"] == fake_content["phrases"]
    assert data["source"] == "live"
    assert data["fetched_at"] == "2026-10-28T15:00:00Z"
    assert data["fetch_error"] is None
    assert data["content_error"] is None


def test_load_app_data_passes_on_cache_source_and_error(monkeypatch, raw_records, fake_content):
    monkeypatch.setattr(loaders, "fetch_country_data", _fake_fetch(raw_records, "cache", "network"))
    data = loaders.load_app_data()
    assert data["source"] == "cache"
    assert data["fetch_error"] == "network"
    assert data["countries"]  # cached countries still load


def test_load_app_data_without_any_data_has_no_countries(monkeypatch, fake_content):
    monkeypatch.setattr(loaders, "fetch_country_data", _fake_fetch([], "none", "network"))
    data = loaders.load_app_data()
    assert data["countries"] == {}
    assert data["source"] == "none"
    assert data["fetched_at"] is None


def test_load_app_data_turns_bad_csv_into_partial_mode(monkeypatch, raw_records):
    def broken():
        raise ValueError('phrases.csv row 14: unknown category "food"')

    monkeypatch.setattr(loaders, "fetch_country_data", _fake_fetch(raw_records))
    monkeypatch.setattr(loaders, "load_curated_content", broken)
    data = loaders.load_app_data()
    assert data["content_error"] == 'phrases.csv row 14: unknown category "food"'
    assert data["phrases"] == data["culture"] == data["photos"] == []
    assert len(data["countries"]) == 4  # country facts still available
