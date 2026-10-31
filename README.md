# CultureQuest

A cultural travel and language companion, built with Python and [Flet](https://flet.dev).

CultureQuest helps travelers prepare for countries whose language and customs are unfamiliar. Search about 250 countries and territories, read each one's key facts, learn useful phrases and cultural notes, and compare destinations side by side. The layout works at phone and desktop widths.

Final project for IS 6495 (Python), MSIS program, University of Utah. Jordon Draper.

| Desktop | Phone |
|---|---|
| ![Japan profile on desktop](docs/screenshots/profile-desktop.png) | ![Japan profile on a phone](docs/screenshots/profile-phone.png) |
| ![Compare on desktop: population chart and language matrix](docs/screenshots/compare-desktop.png) | ![Explore on a phone](docs/screenshots/explore-phone.png) |

## Features

- **Explore:** search countries by name and filter by region. Countries with curated content carry a Phrases badge.
- **Country profile:** flag, key facts (capital, languages, currencies, population), and, for curated countries, a photo, travel phrases by category, and cultural notes with their sources and review dates.
- **Compare (2 to 5 countries):** a population bar chart and a language overlap matrix.
- **Works offline for a while:** country data is cached for up to 3 days. When the live fetch fails, the app uses the cache and says so in a banner.
- **Honest data:** missing values read "Unavailable", and every source is credited in the app.

Curated phrases and cultural notes currently cover **Japan**. Mexico, France, South Korea and Brazil are planned (see [Future work](#future-work)).

## Setup

You need **Python 3.14** and a free **REST Countries API key**.

1. **Get the code**

   ```
   git clone https://github.com/jordondraper/culture-quest.git
   cd culture-quest
   ```

2. **Create and activate a virtual environment**

   macOS / Linux:
   ```
   python3.14 -m venv .venv
   source .venv/bin/activate
   ```

   Windows (PowerShell):
   ```
   py -3.14 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install the dependencies**

   ```
   pip install -r requirements.txt
   ```

4. **Add your API key.** Create a free account at [restcountries.com](https://restcountries.com/) and copy your API key. Then copy the example settings file and paste the key into it:

   ```
   cp .env.example .env
   ```

   `.env` should contain one line:

   ```
   REST_COUNTRIES_API_KEY=your_key_here
   ```

   `.env` is in `.gitignore`, so the key is never committed.

5. **macOS only, python.org installs:** if the app shows "Check your internet connection" while you are online, Python is missing its security certificates. Run **Install Certificates.command** from your `Applications/Python 3.14` folder once, then start the app again.

## Run the app

```
python main.py
```

The app opens in its own window. Resize the window below 768 px wide to see the phone layout. To stop it, press **Ctrl+C** in the terminal.

## Run the tests

```
pytest
ruff check .
```

The tests never touch the network or your real files: API calls are faked and file tests use temporary folders. GitHub Actions runs both commands on every push.

## How it meets the course requirements

| Requirement | Where |
|---|---|
| External data, nothing hardcoded | REST Countries API (`src/api.py`); curated CSV files in `data/` (`src/loaders.py`) |
| Data processing in Python | `src/processing.py`: normalizing, searching, filtering, grouping, building chart data |
| At least 3 programmer-defined functions or classes | `fetch_country_data()`, `normalize_countries()`, `load_curated_content()`, `search_countries()`, `build_country_profile()` from the proposal, plus the `AppState` class and the chart builders |
| A function that transforms data | `normalize_countries()` turns nested API records into flat country dictionaries; `build_language_matrix()` turns countries into a language table |
| At least 2 visualization types | Population bar chart and language overlap matrix (`ui/charts.py`), on the Compare screen |

## Project structure

```
main.py              Starts the app
src/                 Data and logic, no user interface
  api.py             Fetches country data from REST Countries, with a 3-day cache
  loaders.py         Reads and validates the curated CSV files
  processing.py      Pure functions: normalize, search, filter, build profiles and chart data
  state.py           AppState: loaded data and the user's selections
  constants.py       Paths, API settings, categories and limits
ui/                  Flet screens and building blocks
  shell.py           Navigation, banners, phone and desktop layouts
  explore.py, profile.py, compare.py, about.py   The screens
  charts.py          The two visualizations
  components.py      Reusable pieces (cards, chips, buttons)
  theme.py           Colors, type, spacing and sizes
  messages.py        Every user-facing text
data/                phrases.csv, culture.csv, photos.csv (curated content)
tests/               pytest tests and fixtures
docs/                Architecture, decision records (ADRs), design system, wireframes
assets/fonts/        Noto Sans and Noto Sans JP, so Japanese text renders on any computer
```

Design decisions are recorded in [`docs/adr/`](docs/adr/), and the full design is in [`docs/architecture.md`](docs/architecture.md).

## Data sources and credits

- **Country facts and flags:** [REST Countries](https://restcountries.com/). Cached for at most 3 days, as its terms require; cached data is never committed.
- **Phrases:** [Wikivoyage phrasebooks](https://en.wikivoyage.org/wiki/Phrasebooks), CC BY-SA. The phrase list names its phrasebook, and each phrase row in `data/phrases.csv` keeps its source link and review date.
- **Cultural notes:** [Japan National Tourism Organization](https://www.japan.travel/en/) and the [UNESCO Intangible Cultural Heritage lists](https://ich.unesco.org/en/lists). Each note keeps its source link and review date.
- **Photos:** [Wikimedia Commons](https://commons.wikimedia.org/). The photographer and license are shown under each photo.
- **Fonts:** [Noto Sans and Noto Sans JP](https://fonts.google.com/noto), SIL Open Font License.

Cultural notes describe common practice, not universal rules; customs vary by region and community.

## Future work

- Curated phrases and notes for Mexico, France, South Korea and Brazil, as planned in the proposal. The app reads everything from the CSV files, so adding a country needs no code changes (South Korea also needs the Noto Sans KR font).
- Curating content by hand doesn't scale: every phrase and note needs a source, a review and attribution.
- A map of each country's capitals on the profile.
