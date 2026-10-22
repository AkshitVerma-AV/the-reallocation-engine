# Lottery-weight check — 2026-10-19

## Executive summary

**What this is.** Since spring 2026, the H-1B lottery gives an employer's registration more chances when the offered salary sits higher on the government's four-step wage ladder: one entry at the bottom step, up to four at the top. This report takes data-analyst and data-engineer job postings that are open today at companies with a strong sponsorship record, reads the pay range each one publishes, and shows which steps of that ladder the pay could reach.

**Why read it.** The step depends on a job code the employer picks and on local wages, and you see neither. So every answer here is a range, worked out under each job code the employer could reasonably use. Where the code alone changes the answer, the report tells you what to ask the recruiter.

**What it found.** You can reach **3** lottery round(s) before your work permission ends; the next one opens around 2027-03-01, and the employer needs your accepted offer before then. Of 20 data-titled postings on the checked boards, 3 are open, US-based, and not senior, intern or contract roles. Reads: none. 3 item(s) need a human look. No chance of winning is calculated anywhere: the government has not published how many registrations sit at each step.

This report is for the student. The machine log is `lottery-weight.json` beside it.

## Your lottery rounds (gate G0)

| Fiscal year | Registration opens (assumed?) | Reachable | Why not |
|---|---|---|---|
| FY2028 | 2027-03-01 (assumed) | yes | — |
| FY2029 | 2028-03-01 (assumed) | yes | — |
| FY2030 | 2029-03-01 (assumed) | yes | — |
| FY2031 | 2030-03-01 (assumed) | no | opens 2030-03-01, after work authorization ends 2030-01-22 |

Work authorization through **2030-01-22** (opt_end_date + 24 months STEM OPT; your-input). STEM OPT also requires an E-Verify employer, which this report does not check.

## Postings (open today, entry-eligible, US)

_No open entry-eligible US posting reached the wage check._

## Offers and scenarios you entered

| Scenario | Title | Worksite | Base | Lottery read | Entries | Status |
|---|---|---|---|---|---|---|
| A (hypothetical) | Data Analyst | Chicago, IL | $85,000 | — | — | MANUAL-CHECK: soc-map-not-confirmed (G3: family 'data-analyst' awaits a human) |
| B (hypothetical) | Business Intelligence Analyst | Boston, MA | $72,000 | — | — | MANUAL-CHECK: soc-map-not-confirmed (G3: family 'business-intelligence' awaits a human) |
| C (hypothetical) | Data Engineer | New York, NY | $105,000 | — | — | MANUAL-CHECK: soc-map-not-confirmed (G3: family 'data-engineer' awaits a human) |
| D (hypothetical) | Product Analyst | Chicago, IL | $90,000 | — | — | MANUAL-CHECK: title-not-in-soc-map (G3: add a family or skip) |

## Needs a human look

| Company | Posting / item | Reason | Next action |
|---|---|---|---|
| KLAVIYO INC | Analytics Engineer | soc-map-not-confirmed (G3: family 'analytics-engineer' awaits a human) | read the posting by hand (soc-map-not-confirmed (G3: family 'analytics-engineer' awaits a human)) |
| SIGMA COMPUTING INC | Data Engineer | soc-map-not-confirmed (G3: family 'data-engineer' awaits a human) | read the posting by hand (soc-map-not-confirmed (G3: family 'data-engineer' awaits a human)) |
| SIGMA COMPUTING INC | Data Engineer | soc-map-not-confirmed (G3: family 'data-engineer' awaits a human) | read the posting by hand (soc-map-not-confirmed (G3: family 'data-engineer' awaits a human)) |

## What this report cannot tell you

- **The real wage step.** The ladder used here is the *national* one from May 2024. The government's table for your worksite (July 2026 – June 2027, built on May 2025 data) is not in the repo. In expensive cities local wages run higher, so these steps are likely **too generous** there.
- **The job code.** The employer's immigration lawyer chooses it after the offer. The codes listed are the plausible ones a human approved, not the one that will be filed.
- **Your odds.** Entries are not odds; nobody outside the government knows the pool by step.
- **Pay you will be offered.** A posted range is not an offer. The floor is used because an offer can land there.
- **Company median salary** in the sponsorship data covers *all* sponsored titles (mostly software engineers). It is shown for context and never compared with a data-role posting.

## Human gate G4

- [ ] I read every `parsed-text` quote below and it matches the posting.
- [ ] I checked the plausible job codes for each family (gate G3) before trusting any read.
- Signed: ______________________ Date: __________

## Run record

- Recipe `data-lottery-weight` v0.1.0 · as_of 2026-10-19 · board mode live
- Persona `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json` (fictional: True) · SOC map `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json` (confirmed by: nobody yet)
- Wage ladder `data/bls/oesm24nat/national_M2024_dl.xlsx (BLS OEWS May 2024, national, detailed occupations)` · sponsorship `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` · scorer `scripts/score/role-scorer.mjs`
- Audit: boards fetched 16 (unresolved 0) · postings on boards 1264 · data-titled 20 · excluded senior/intern/contract 14 · excluded non-US 3 · entry-eligible US 3
- Scorer timeline factor 1.0 (slack 90 days; factor = min(1, (opt_start + ceiling − max(as_of + lag, opt_start)) / ceiling))
