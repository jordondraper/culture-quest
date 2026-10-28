# ADR-0001: Country data source and caching

- **Status:** Proposed
- **Date:** 2026-10-27
- **Deciders:** Jordon Draper (with instructor input)

## Context

CultureQuest needs worldwide country facts (names, codes, capitals, regions, languages, currencies, population). The project proposal names the REST Countries API v5 as the source.

REST Countries terms and limits that affect the design:

- Bearer-token authentication; a free key allows 1,000 requests per month and 20 requests per 10 seconds.
- Cached data may be kept for **at most 3 days**; no long-term storage or offline copies.
- No bulk redistribution, so cached data cannot be committed to the repository or included in the submission.
- Attribution to REST Countries, with a link, is required in the app.

Consequence: anyone running the project, including the instructor, needs their own API key, and the app cannot ship with saved data for offline use.

## Options considered

### A. REST Countries with a 3-day expiring cache (current plan)

- Matches the proposal exactly.
- Cache in `data/cache/` (gitignored), deleted when older than 3 days.
- Graders must create a REST Countries account and key to run the app.

### B. `mledoze/countries` dataset plus the World Bank Indicators API

- Country facts from a JSON dataset licensed ODbL 1.0, which may be committed with attribution. Flag emoji only, since flag images are licensed separately.
- Population from the World Bank API (`SP.POP.TOTL`), which needs no key.
- No API key or `.env` required; the committed dataset doubles as a reliable fallback.
- Changes the data source named in the proposal, so it requires instructor approval. World Bank terms of use still need to be checked.

### C. REST Countries with a separate grading-only key

- Shared privately with the instructor and revoked after grading.
- Keeps the proposal unchanged and lets the instructor run the app.
- Depends on whether REST Countries terms allow sharing a key this way (not yet confirmed with their support).

## Decision

Pending. An email to the instructor asks (1) whether he will run the app himself and (2) whether a data source change is acceptable.

## Consequences

**Whichever option is chosen, the architecture is unaffected outside the data-access layer.** Only `src/api.py` and the raw-field mapping inside `normalize_countries()` change; the country contract (architecture.md, Section 3.1) and all other modules stay the same.

Once decided, this ADR is updated to Accepted, and User Stories v1.2 updates US-08 (offline fallback) and TR-05 (submission package), and adds an attribution acceptance criterion for the chosen source.

- **If A:** README must explain how to obtain a key; offline fallback only works within 3 days of a successful fetch.
- **If B:** remove the `.env` dependency and 3-day rule from Sections 1, 3.2, and 4.2; add ODbL and World Bank attribution to the About screen.
- **If C:** same as A for the code; add a key-revocation step to the release checklist.
