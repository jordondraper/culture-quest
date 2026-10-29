"""Shared pytest fixtures."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def raw_records() -> list[dict]:
    """Hand-written raw v5 records: Japan, South Africa, Switzerland, Antarctica, Testland.

    Loaded fresh for every test, so a test can change its copy without affecting others.
    """
    with open(FIXTURES_DIR / "raw_countries.json", encoding="utf-8") as file:
        return json.load(file)
