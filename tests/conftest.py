"""Shared pytest fixtures."""

import json
from pathlib import Path

import pytest

from src.loaders import load_curated_content
from src.processing import normalize_countries

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def raw_records() -> list[dict]:
    """Hand-written raw v5 records: Japan, South Africa, Switzerland, Antarctica, Testland.

    Loaded fresh for every test, so a test can change its copy without affecting others.
    """
    with open(FIXTURES_DIR / "raw_countries.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def countries(raw_records) -> dict[str, dict]:
    """The fixture records after normalize_countries(): JP, ZA, CH and AQ."""
    return normalize_countries(raw_records)


@pytest.fixture
def content() -> dict[str, list[dict]]:
    """The three valid fixture CSVs through load_curated_content()."""
    return load_curated_content(
        FIXTURES_DIR / "phrases_valid.csv",
        FIXTURES_DIR / "culture_valid.csv",
        FIXTURES_DIR / "photos_valid.csv",
    )
