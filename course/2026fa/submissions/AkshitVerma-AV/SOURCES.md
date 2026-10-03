# SOURCES

## Executive summary

This file lists what this submission is built on (repository, governing
documents, data, tools) and splits the work between me and the AI agent. Short
version: I chose the situation, the persona, the design decisions and the gate
sign-offs. The AI agent (Claude Code) wrote most of the text and code under my
direction, and I reviewed it. Details are below, and in FRICTIONAL.md with dates.

## Repository and governing documents

- *The Reallocation Engine*, Nik Bear Brown / Humanitarians AI: forked from
  `nikbearbrown/the-reallocation-engine` to `AkshitVerma-AV/the-reallocation-engine`.
- `SNICKERDOODLE.md` (prime directive, gates), `DOMAIN.md` (known gaps),
  `CONTRIBUTING.md` (namespaces), `DATA_CONTRACT.md` §Zero-Conditions,
  `recipes/README.md`, `recipes/_shared.md` (run-log format).
- Style models: `recipes/scan.md`, `recipes/local-wage-adjustment.md`,
  `recipes/local-wage-adjustment.card.md`.
- `book/chapters/07-who-sponsors-the-80-days-sponsorship-scorer.md`: the tier
  vocabulary, and the statement that the tier thresholds are unreconciled.
- `scripts/score/role-scorer.mjs`: the decision core, called and not copied.
- `scripts/ats/providers/{greenhouse,lever,ashby}.mjs`: the public board endpoints.
- `scripts/ats/check-liveness.mjs` (`npm run ats:liveness`): the independent cross-check.

## Data

| Data | Path | Used for |
|---|---|---|
| 80 Days to Stay CSV (v3) | `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | sponsorship counts, top sponsored titles, funding dates |
| 80 Days audit | `data/80-days-to-stay/data/SEC_DOL_H1b_data_mapped-audit.md` | coverage (5.1% of rows with H-1B fields), no SOC codes |
| SEC Form D samples | `data/sec/form-d/processed/sample/*.sample.json` (4 × 50 companies) | funding recency join |
| BLS OEWS / O*NET compact | `data/bls/compact/soc_occupation_compact.csv` | national median wage, as context |
| Live ATS board APIs | `boards-api.greenhouse.io`, `api.lever.co`, `api.ashbyhq.com` | open postings on 2026-10-03 |

The 3-3-2 split comes from Nik Bear Brown, *The 3-3-2 Split: Why Your Job Search
Is Probably Backwards*. I cite none of the essay's figures as records.

## Tools

Claude Code (Opus 5.5) as the coding agent; Node 24.19; Python 3.12 (standard
library only); Playwright Chromium (for `ats:liveness`); Git for Windows; VS Code.

## Human vs. AI contributions

| Part | AI agent | Me (Akshit) |
|---|---|---|
| Situation and angle | proposed option lists | **chose** the target situation (MSIS → Data Analyst/Engineer, F-1 pre-OPT), network-targets, step-by-step mode |
| Persona | — | **chose** Jack Spencer, Dec 2026 graduation, OPT start 2027-01-23, Chicago |
| Data measurements (121→123 candidates, funding counts, Form D join) | ran and reported | reviewed |
| CHANGE-BRIEF.md | drafted | accepted without edits; revisions appended for my decisions |
| Recipe and card | drafted | **accepted** tier rule, fit omission, empty-board = unresolved; **changed** funding to a NETWORK requirement |
| OPT-end and hiring-lag defaults | proposed (labeled your-input) | accepted |
| Board slugs (`boards.json`) | proposed by probing the named APIs | **confirmed** all 16 at G1 |
| Prototype and tests | wrote | reviewed; directed the v0.1.1 fix |
| Zoox false positive | found it on reading run-1 | **decided** the exclusion and the run-2 replay approach |
| Senior-only flag | proposed | **decided** flag only, no bucket change |
| G3 sign-off | — | **signed** |
| Worked run, domain justification, run log, this file | drafted from real output | reviewed in chat; asked the agent to fill my FRICTIONAL `[ME]` blanks. Each such fill is marked "AI-drafted at Akshit's request, accepted by Akshit". The G3 outreach choice is mine, recorded without personal details |
| Things I rejected from the AI | funding as a ranking aid only (I made it a requirement) | nothing else rejected. I extended the AI's persona exclusions after run-1 (contract / student worker / part-time) and chose flag-only for senior-only evidence |
