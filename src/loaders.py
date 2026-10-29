"""Data access for curated content: phrases.csv, culture.csv and photos.csv.

These files are part of the project, so a problem in them is a development error:
load_curated_content() raises ValueError naming the file, the row and the problem,
and main.py runs the app in partial mode.
"""

import csv
import re
from datetime import date
from pathlib import Path

from src.constants import (
    CULTURE_COLUMNS,
    CULTURE_OPTIONAL,
    CULTURE_PATH,
    PHOTO_COLUMNS,
    PHOTO_OPTIONAL,
    PHOTOS_PATH,
    PHRASE_CATEGORIES,
    PHRASE_COLUMNS,
    PHRASE_OPTIONAL,
    PHRASES_PATH,
)

Row = dict[str, str]

# Two uppercase letters, like "JP". re.fullmatch must match the whole value.
_COUNTRY_CODE = re.compile(r"[A-Z]{2}")


# --- Public function ---


def load_curated_content(
    phrase_path: Path = PHRASES_PATH,
    culture_path: Path = CULTURE_PATH,
    photo_path: Path = PHOTOS_PATH,
) -> dict[str, list[Row]]:
    """Read and validate the three curated CSV files.

    Args:
        phrase_path, culture_path, photo_path: The CSV files. Tests pass small
            fixture files; normal calls pass no arguments.

    Returns:
        {"phrases": [...], "culture": [...], "photos": [...]}, each a list of row
        dicts with exactly the expected columns, values trimmed of spaces.

    Raises:
        ValueError: A file is missing, a column is missing, or a row breaks a rule.
            The message names the file and row, e.g.
            'phrases.csv row 14: unknown category "food"'.
    """
    phrases = _read_csv(phrase_path, PHRASE_COLUMNS, PHRASE_OPTIONAL)
    for line, row in phrases:
        if row["category"] not in PHRASE_CATEGORIES:
            _fail(phrase_path, line, f'unknown category "{row["category"]}"')
    _reject_duplicates(phrase_path, phrases, ("country_code", "english"))

    culture = _read_csv(culture_path, CULTURE_COLUMNS, CULTURE_OPTIONAL)
    _reject_duplicates(culture_path, culture, ("country_code", "topic"))

    photos = _read_csv(photo_path, PHOTO_COLUMNS, PHOTO_OPTIONAL)
    for line, row in photos:
        _check_url(photo_path, line, row, "image_url")
    _reject_duplicates(photo_path, photos, ("country_code",))  # one photo per country

    return {
        "phrases": [row for _, row in phrases],
        "culture": [row for _, row in culture],
        "photos": [row for _, row in photos],
    }


# --- Reading and shared row checks ---


def _read_csv(
    path: Path, columns: tuple[str, ...], optional: frozenset[str]
) -> list[tuple[int, Row]]:
    """Read a CSV and run the checks every file shares.

    Returns (line number, row) pairs. The line number matches what a spreadsheet
    shows: the header is line 1, so the first data row is line 2.
    """
    try:
        # utf-8-sig also accepts the invisible "byte order mark" some spreadsheet
        # apps put at the start of a file, which would otherwise end up in the
        # first column's name.
        with open(path, encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            header = reader.fieldnames or []
            rows = list(enumerate(reader, start=2))
    except FileNotFoundError:
        raise ValueError(f"{path.name}: file not found at {path}") from None
    except UnicodeDecodeError:
        raise ValueError(f"{path.name}: not saved as UTF-8") from None

    missing = [column for column in columns if column not in header]
    if missing:
        raise ValueError(f"{path.name}: missing column(s) {', '.join(missing)}")

    checked = []
    for line, raw in rows:
        # Keep only the expected columns, trimmed. A short row gives None values.
        row = {column: (raw.get(column) or "").strip() for column in columns}
        if not any(row.values()):
            continue  # skip fully blank lines, such as one left at the end of the file
        for column in columns:
            if column not in optional and not row[column]:
                _fail(path, line, f"{column} is empty")
        if not _COUNTRY_CODE.fullmatch(row["country_code"]):
            _fail(path, line, f'country_code "{row["country_code"]}" is not two capital letters')
        _check_url(path, line, row, "source_url")
        if "reviewed_on" in row:
            _check_date(path, line, row["reviewed_on"])
        checked.append((line, row))
    return checked


def _check_url(path: Path, line: int, row: Row, column: str) -> None:
    if not row[column].startswith("https://"):
        _fail(path, line, f"{column} must start with https://")


def _check_date(path: Path, line: int, value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError:
        _fail(path, line, f'reviewed_on "{value}" is not a YYYY-MM-DD date')


def _reject_duplicates(path: Path, rows: list[tuple[int, Row]], key: tuple[str, ...]) -> None:
    """Fail on the second row that repeats the same values in the key columns."""
    first_seen: dict[tuple[str, ...], int] = {}
    for line, row in rows:
        value = tuple(row[column] for column in key)
        if value in first_seen:
            _fail(path, line, f"duplicate of row {first_seen[value]} ({', '.join(value)})")
        first_seen[value] = line


def _fail(path: Path, line: int, problem: str) -> None:
    raise ValueError(f"{path.name} row {line}: {problem}")
