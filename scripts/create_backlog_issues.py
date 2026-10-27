"""Create the CultureQuest backlog as GitHub issues.

Reads the user stories and technical requirements from User Stories v1.1,
creates any missing labels and milestones, then creates one issue per
backlog item. Items whose title already exists in the repo are skipped,
so the script is safe to run more than once.

Usage (from the repo folder):
    python3 scripts/create_backlog_issues.py --dry-run   # preview only
    python3 scripts/create_backlog_issues.py             # create issues

Requires the GitHub CLI (gh), signed in with `gh auth login`.
"""

import json
import subprocess
import sys

REPO = "jordondraper/culture-quest"

LABELS = {
    "story": ("1D76DB", "User story"),
    "tech-req": ("5319E7", "Technical requirement (enabler)"),
    "required": ("B60205", "Fulfills a graded course or proposal requirement"),
    "stretch": ("C5DEF5", "Stretch goal"),
    "area: data": ("0E8A16", "Data layer: API, CSVs, processing"),
    "area: ui": ("0E8A16", "Flet interface"),
    "area: viz": ("0E8A16", "Charts and matrix"),
}

M1 = "M1 – Japan vertical slice"
M2 = "M2 – Five-country MVP"
M3 = "M3 – Release v1.0"
MILESTONES = [M1, M2, M3]

# Each item: title, priority, labels, milestone, story or description,
# and a list of acceptance criteria (shown as a checklist).
ITEMS = [
    {
        "title": "US-01: Destination Discovery",
        "priority": "P0", "labels": ["story", "required", "area: data", "area: ui"], "milestone": M1,
        "story": "As a traveler preparing to visit a culturally unfamiliar country, I want to search for destinations by name or region, so that I can easily find information about the country I plan to visit.",
        "criteria": [
            'AC-01.1 Partial, case-insensitive name search ("kor" returns North and South Korea)',
            "AC-01.2 Region filter applies together with any name search",
            "AC-01.3 Results sorted alphabetically",
            "AC-01.4 No-results message suggests changing the search or filter",
            "AC-01.5 Clearing search and filter restores the full alphabetical list",
            "AC-01.6 Selecting a result opens its country profile",
        ],
    },
    {
        "title": "US-02: Country Information",
        "priority": "P0", "labels": ["story", "required", "area: data", "area: ui"], "milestone": M1,
        "story": "As a traveler visiting an unfamiliar destination, I want to view essential country information, including languages, currencies, and geographic details, so that I can better understand my destination before traveling.",
        "criteria": [
            "AC-02.1 Profile shows name, capital, region, languages, currencies, and population",
            "AC-02.2 All capitals and languages shown when there are several",
            'AC-02.3 Missing fields labeled "Unavailable"',
            "AC-02.4 Population formatted with thousands separators",
        ],
    },
    {
        "title": "US-03: Cultural Etiquette and Heritage",
        "priority": "P0", "labels": ["story", "required", "area: data", "area: ui"], "milestone": M1,
        "story": "As a traveler unfamiliar with local customs, I want to learn about common etiquette and important cultural traditions, so that I can interact respectfully, avoid unintentional misunderstandings, and appreciate my destination's heritage before visiting.",
        "criteria": [
            "AC-03.1 Destination's 4–6 curated notes are displayed",
            "AC-03.2 Each note has a topic and a 1–3 sentence plain-language summary",
            "AC-03.3 Each note is labeled etiquette or heritage",
            "AC-03.4 Regional or community context shown; practices not presented as universal",
            "AC-03.5 Source and review date visible on each note",
            "AC-03.6 Message shown when a destination has no cultural notes",
        ],
    },
    {
        "title": "US-04: Travel Phrases with Romanization",
        "priority": "P0", "labels": ["story", "required", "area: data", "area: ui"], "milestone": M1,
        "story": "As a traveler who does not speak the local language, I want to access essential phrases with their English meanings and, where the writing system is unfamiliar, a romanized version, so that I can prepare for basic conversations and attempt to pronounce useful expressions.",
        "criteria": [
            "AC-04.1 Destination's 10–15 curated phrases are displayed",
            "AC-04.2 Each phrase shows original-language text and English meaning",
            "AC-04.3 Romanization shown when available and visually distinct from the original",
            "AC-04.4 No empty romanization line when romanization is unavailable",
            "AC-04.5 Non-Latin characters and accents render correctly",
            "AC-04.6 Phrases appear only under their own destination",
            "AC-04.7 Wikivoyage credited, with its Creative Commons share-alike license noted",
            "AC-04.8 Message shown when a destination has no phrases",
        ],
    },
    {
        "title": "US-05: Categorized Language Phrases",
        "priority": "P0", "labels": ["story", "required", "area: ui"], "milestone": M1,
        "story": "As a traveler preparing for everyday interactions, I want to browse phrases by categories such as greetings, dining, and transportation, so that I can focus on language relevant to situations I expect to encounter.",
        "criteria": [
            "AC-05.1 Categories come from a fixed, application-wide list",
            "AC-05.2 Selecting a category shows only matching phrases for the destination",
            "AC-05.3 Changing category updates the list",
            "AC-05.4 Categories with no phrases for the destination are hidden or disabled",
            "AC-05.5 Clearing the filter shows all phrases for the destination",
        ],
    },
    {
        "title": "US-06: Population Comparison Chart",
        "priority": "P0", "labels": ["story", "required", "area: viz"], "milestone": M2,
        "story": "As a traveler considering several destinations, I want to compare their populations in a bar chart, so that I can understand the relative size of the places I am considering.",
        "criteria": [
            "AC-06.1 User can select two to five countries",
            "AC-06.2 Fewer than two or more than five: chart not generated, limit explained",
            "AC-06.3 One bar per country, labeled with the country name",
            "AC-06.4 Values use abbreviated labels (125M, not 125000000)",
            'AC-06.5 Missing population labeled "Data unavailable", not drawn as zero',
            "AC-06.6 Readable at mobile and desktop widths",
        ],
    },
    {
        "title": "US-07: Language Comparison Matrix",
        "priority": "P0", "labels": ["story", "required", "area: viz"], "milestone": M2,
        "story": "As a traveler considering multiple destinations, I want to compare the languages associated with different countries, so that I can understand which destinations share languages and prepare accordingly.",
        "criteria": [
            "AC-07.1 Selected countries are rows, using the population chart's selection",
            "AC-07.2 Languages are columns, matched by ISO code so each appears once",
            "AC-07.3 Cells marked where a country lists a language",
            "AC-07.4 Shared languages accurately reflected",
            "AC-07.5 Missing language information clearly indicated",
            "AC-07.6 Caption: matrix shows API-listed languages only, not every language community",
        ],
    },
    {
        "title": "US-08: Offline Data Fallback",
        "priority": "P0", "labels": ["story", "required", "area: data"], "milestone": M1,
        "story": "As a traveler, I want CultureQuest to keep working when the country data service is unavailable, so that a network or service problem doesn't stop me from preparing for my trip.",
        "criteria": [
            "AC-08.1 On API failure (no connection, invalid key, rate limit, frozen account), load the saved snapshot",
            'AC-08.2 Notice shown: "Showing saved data from [snapshot date]"',
            "AC-08.3 Phrases and cultural notes still load from local CSVs",
            "AC-08.4 No snapshot available: clear message, no crash",
            "AC-08.5 Successful request saves a new dated snapshot",
        ],
        "note": "Caching approach under review: REST Countries terms limit cached data to 3 days. Criteria will be updated in User Stories v1.2.",
    },
    {
        "title": "US-09: Quick On-Trip Reference",
        "priority": "P1", "labels": ["story", "area: ui"], "milestone": M2,
        "story": "As a traveler currently visiting an unfamiliar destination, I want to quickly retrieve previously viewed phrases and cultural guidance, so that I can reference useful information during real-world interactions.",
        "criteria": [
            "AC-09.1 Phrase and cultural sections reachable through clearly labeled navigation",
            "AC-09.2 Category navigation without another destination search",
            "AC-09.3 Readable at about 380px wide with no horizontal scrolling",
            "AC-09.4 User stays within the same destination profile when navigating back",
        ],
    },
    {
        "title": "US-10: Save Important Travel Information",
        "priority": "P2", "labels": ["story", "stretch", "area: data", "area: ui"], "milestone": M3,
        "story": "As a traveler preparing for an international trip, I want to save useful phrases and cultural notes, so that I can easily revisit important information before and during my travels.",
        "criteria": [
            "AC-10.1 Save adds a phrase or note to a saved-items collection",
            "AC-10.2 Saved collection displays saved items",
            "AC-10.3 Saved items open with full content",
            "AC-10.4 Removed items no longer appear",
            "AC-10.5 Saved items persist after closing and reopening the app",
        ],
        "note": "Stretch goal. Start only after all P0 and P1 stories meet the Definition of Done.",
    },
    {
        "title": "TR-01: Programmer-Defined Functions",
        "priority": "P0", "labels": ["tech-req", "required", "area: data"], "milestone": M1,
        "story": "Implement at least the five functions named in the proposal, kept separate from the Flet interface code. The course minimum is three.",
        "criteria": [
            "fetch_country_data()",
            "normalize_countries(raw_records)",
            "load_curated_content(phrase_path, culture_path)",
            "search_countries(countries, query, region=None)",
            "build_country_profile(country_code, countries, phrases, culture)",
            "No function above imports or calls Flet",
        ],
    },
    {
        "title": "TR-02: Data Transformation",
        "priority": "P0", "labels": ["tech-req", "required", "area: data"], "milestone": M1,
        "story": "normalize_countries() transforms nested API JSON into flat country dictionaries keyed by ISO alpha-2 code.",
        "criteria": [
            "Output keyed by uppercase ISO alpha-2 code",
            "Multiple capitals and languages preserved",
            "Missing values labeled unavailable",
            "Unit tests cover a multi-capital country, a multilingual country, and a record with missing fields",
        ],
    },
    {
        "title": "TR-03: External Data Only",
        "priority": "P0", "labels": ["tech-req", "required", "area: data"], "milestone": M1,
        "story": "No country, phrase, or cultural content is hardcoded. All content loads at runtime from the REST Countries API, the saved snapshot, phrases.csv, or culture.csv.",
        "criteria": [
            "No country facts, phrases, or notes appear in Python source files",
            "API key read from .env, never committed",
        ],
    },
    {
        "title": "TR-04: Data File Standards",
        "priority": "P0", "labels": ["tech-req", "required", "area: data"], "milestone": M2,
        "story": "phrases.csv and culture.csv use UTF-8 encoding, contain all required columns, and record a source URL and review date on every row.",
        "criteria": [
            "Both files saved as UTF-8",
            "All required columns present",
            "Source URL and review date on every row",
            "load_curated_content() rejects missing columns and unknown country codes",
        ],
    },
    {
        "title": "TR-05: Submission Package",
        "priority": "P0", "labels": ["tech-req", "required"], "milestone": M3,
        "story": "The final submission includes everything the course and proposal require.",
        "criteria": [
            "Application source code",
            "Curated data files (phrases.csv, culture.csv)",
            "README with setup instructions, including how to get an API key",
            "Written reflection",
            "Walkthrough video (desktop and mobile widths)",
            "Components listed in the final submission assignment (pending)",
        ],
    },
]


def gh(*args, check=True):
    """Run a gh command and return its output as text."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def build_body(item):
    """Turn one backlog item into Markdown for the issue body."""
    is_story = "story" in item["labels"]
    required = "Yes" if "required" in item["labels"] else "No"
    lines = [
        f"**{'Story' if is_story else 'Requirement'}:** {item['story']}",
        "",
        f"**Priority:** {item['priority']} · **Required by proposal:** {required}",
        f"**Spec:** User Stories and Acceptance Criteria v1.1, {item['title'].split(':')[0]}",
        "",
        "### Acceptance criteria" if is_story else "### Done when",
    ]
    lines += [f"- [ ] {c}" for c in item["criteria"]]
    if item.get("note"):
        lines += ["", f"> **Note:** {item['note']}"]
    lines += ["", "### Definition of Done", "See Appendix B of the user stories document."]
    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY RUN: nothing will be created.\n")
        for item in ITEMS:
            print("=" * 70)
            print(item["title"], "|", ", ".join(item["labels"]), "|", item["milestone"])
            print(build_body(item))
        return

    # 1. Labels: --force updates a label if it already exists.
    for name, (color, description) in LABELS.items():
        gh("label", "create", name, "--color", color,
           "--description", description, "--force", "--repo", REPO)
    print("Labels ready.")

    # 2. Milestones: create only the ones that don't exist yet.
    existing = json.loads(gh("api", f"repos/{REPO}/milestones?state=all"))
    existing_titles = {m["title"] for m in existing}
    for title in MILESTONES:
        if title not in existing_titles:
            gh("api", f"repos/{REPO}/milestones", "-f", f"title={title}")
    print("Milestones ready.")

    # 3. Issues: skip any title that already exists (e.g. a hand-made US-01).
    issues = json.loads(gh("issue", "list", "--repo", REPO, "--state", "all",
                           "--limit", "200", "--json", "title"))
    issue_titles = {i["title"] for i in issues}

    for item in ITEMS:
        if item["title"] in issue_titles:
            print(f"Skipped (already exists): {item['title']}")
            continue
        args = ["issue", "create", "--repo", REPO,
                "--title", item["title"], "--body", build_body(item),
                "--milestone", item["milestone"]]
        for label in item["labels"]:
            args += ["--label", label]
        url = gh(*args).strip()
        print(f"Created: {item['title']}  {url}")

    print("\nDone. Set each item's Priority on the project board.")


if __name__ == "__main__":
    main()