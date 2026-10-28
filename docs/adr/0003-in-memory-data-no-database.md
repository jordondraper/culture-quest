# ADR-0003: In-memory dictionaries, no database

- **Status:** Accepted
- **Date:** 2026-10-27
- **Deciders:** Jordon Draper

## Context

The app works with about 250 country records, roughly 50–150 phrase rows, and 20–60 cultural notes. All of it is read-only at runtime. The main operations are lookup by country code, partial-text search, filtering by region or category, and joining the three datasets by country code. The proposal states that countries will be stored in a dictionary keyed by country code, with phrases and cultural notes as lists of dictionaries.

## Options considered

- **In-memory dictionaries and lists:** standard library only; instant lookup by code; data loaded once at startup.
- **SQLite:** good for larger or changing data and for persistence, but adds a schema, SQL, and a build step for data that never changes while the app runs.
- **pandas DataFrames:** convenient for analysis and joins, but a heavy dependency for this data volume, and less natural to pass into UI components than plain dictionaries.

## Decision

Hold all data in memory: `countries` as a dictionary keyed by ISO alpha-2 code, and `phrases` and `culture` as lists of dictionaries, stored in `AppState` (architecture.md, Sections 2 and 3).

## Consequences

- Lookups such as `countries["JP"]` are instant, and searches over 250 records need no indexing.
- Because all data is loaded at startup, individual screens never need loading states (Section 5.4).
- Domain functions take and return plain data, which keeps them pure and easy to test.
- There is no persistence layer. If the stretch story US-10 (saved items) is built, it will need a small separate file for user data rather than a database.
- If curated content grew to thousands of rows across many countries, this decision would be worth revisiting.
