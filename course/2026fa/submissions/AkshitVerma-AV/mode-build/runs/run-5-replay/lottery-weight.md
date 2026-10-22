# Lottery-weight check — 2026-10-19

## Executive summary

**What this is.** Since spring 2026, the H-1B lottery gives an employer's registration more chances when the offered salary sits higher on the government's four-step wage ladder: one entry at the bottom step, up to four at the top. This report takes data-analyst and data-engineer job postings that are open today at companies with a strong sponsorship record, reads the pay range each one publishes, and shows which steps of that ladder the pay could reach.

**Why read it.** The step depends on a job code the employer picks and on local wages, and you see neither. So every answer here is a range, worked out under each job code the employer could reasonably use. Where the code alone changes the answer, the report tells you what to ask the recruiter.

**What it found.** You can reach **3** lottery round(s) before your work permission ends; the next one opens around 2027-03-01, and the employer needs your accepted offer before then. Of 20 data-titled postings on the checked boards, 3 are open, US-based, and not senior, intern or contract roles; at their posted minimum pay, 1 cannot be settled with the national ladder; 2 reach at least the second step under every plausible job code. 0 item(s) need a human look. No chance of winning is calculated anywhere: no published count of registrations at each step was found.

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

| Company | Posting | Location | Posted base (source) | Lottery read (floor, every plausible SOC) | Entries at floor | Scorer | Next action |
|---|---|---|---|---|---|---|---|
| KLAVIYO INC | [Analytics Engineer](https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003) | Boston, MA | $112,000–$168,000 (structured) | **BRACKET-UNRESOLVED** | 1–2 | Apply (0.315) | the national ladder cannot settle the level; check the OFLC wage table for the worksite before negotiating |
| SIGMA COMPUTING INC | [Data Engineer](https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003) | New York City, NY | $140,000–$180,000 (parsed-text) | **CLEARS-LEVEL-II** | 3–4 | Apply (0.315) | apply/tailor if the scorer agrees; the floor already earns 2+ entries under every plausible SOC (national proxy) |
| SIGMA COMPUTING INC | [Data Engineer](https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003) | San Francisco, CA | $140,000–$180,000 (parsed-text) | **CLEARS-LEVEL-II** | 3–4 | Apply (0.315) | apply/tailor if the scorer agrees; the floor already earns 2+ entries under every plausible SOC (national proxy) |

### KLAVIYO INC — Analytics Engineer · floor $112,000 / ceiling $168,000 · family `analytics-engineer`

| SOC | Occupation (OEWS) | P10 · P25 · P50 · P75 · P90 | Floor percentile | Level now | Entries now | Level if DOL proposal took effect | Why plausible |
|---|---|---|---|---|---|---|---|
| 15-2051 | Data Scientists | $63,650 · $82,630 · $112,590 · $155,810 · $194,410 | P25–P50 | I–II | 1–2 | below I–I | analytics engineering sits on the analysis side of data work; no O*NET alternate title 'Analytics Engineer' in the sample (your-input) |
| 15-1243 | Database Architects | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P25–P50 | I–II | 1–2 | below I–I | builds warehouse models and pipelines (Database Architects / Data Warehousing Specialists) (your-input) |
| 15-1252 | Software Developers | $79,850 · $103,050 · $133,080 · $169,000 · $211,450 | P25–P50 | I–II | 1–2 | below I–I | data-platform engineering roles are often filed as Software Developers (your-input) |

### SIGMA COMPUTING INC — Data Engineer · floor $140,000 / ceiling $180,000 · family `data-engineer`

| SOC | Occupation (OEWS) | P10 · P25 · P50 · P75 · P90 | Floor percentile | Level now | Entries now | Level if DOL proposal took effect | Why plausible |
|---|---|---|---|---|---|---|---|
| 15-1243 | Database Architects | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P50–P75 | III–IV | 3–4 | I–III | O*NET 15-1243.00 / 15-1243.01 list 'Big Data Engineer' (record) |
| 15-1242 | Database Administrators | $56,820 · $76,100 · $104,620 · $132,850 · $160,890 | P75–P90 | IV | 4 | III–IV | O*NET 15-1242.00 Database Administrators lists 'Data Engineer' (record) |
| 15-1252 | Software Developers | $79,850 · $103,050 · $133,080 · $169,000 · $211,450 | P50–P75 | III–IV | 3–4 | I–III | data-platform engineering roles are often filed as Software Developers (your-input) |

### SIGMA COMPUTING INC — Data Engineer · floor $140,000 / ceiling $180,000 · family `data-engineer`

| SOC | Occupation (OEWS) | P10 · P25 · P50 · P75 · P90 | Floor percentile | Level now | Entries now | Level if DOL proposal took effect | Why plausible |
|---|---|---|---|---|---|---|---|
| 15-1243 | Database Architects | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P50–P75 | III–IV | 3–4 | I–III | O*NET 15-1243.00 / 15-1243.01 list 'Big Data Engineer' (record) |
| 15-1242 | Database Administrators | $56,820 · $76,100 · $104,620 · $132,850 · $160,890 | P75–P90 | IV | 4 | III–IV | O*NET 15-1242.00 Database Administrators lists 'Data Engineer' (record) |
| 15-1252 | Software Developers | $79,850 · $103,050 · $133,080 · $169,000 · $211,450 | P50–P75 | III–IV | 3–4 | I–III | data-platform engineering roles are often filed as Software Developers (your-input) |

### A — Data Analyst · floor $85,000 · family `data-analyst`

| SOC | Occupation (OEWS) | P10 · P25 · P50 · P75 · P90 | Floor percentile | Level now | Entries now | Level if DOL proposal took effect | Why plausible |
|---|---|---|---|---|---|---|---|
| 15-2051 | Data Scientists | $63,650 · $82,630 · $112,590 · $155,810 · $194,410 | P25–P50 | I–II | 1–2 | below I–I | O*NET 15-2051.00 Data Scientists lists 'Data Analyst' (record) |
| 15-2041 | Statisticians | $60,390 · $79,210 · $103,300 · $137,610 · $170,700 | P25–P50 | I–II | 1–2 | below I–I | O*NET 15-2041.00 Statisticians lists 'Data Analyst' (record) |
| 15-1243 | Database Architects | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P10–P25 | below I–I | 1 | below I | O*NET 15-1243.00 Database Architects lists 'Data Analyst' (record) |
| 13-1161 | Market Research Analysts and Marketing Specialists | $42,070 · $56,220 · $76,950 · $104,870 · $144,610 | P50–P75 | III–IV | 3–4 | I–III | marketing/growth data-analyst roles are often filed as Market Research Analysts (your-input) |

### B — Business Intelligence Analyst · floor $72,000 · family `business-intelligence`

| SOC | Occupation (OEWS) | P10 · P25 · P50 · P75 · P90 | Floor percentile | Level now | Entries now | Level if DOL proposal took effect | Why plausible |
|---|---|---|---|---|---|---|---|
| 15-2051 | Data Scientists | $63,650 · $82,630 · $112,590 · $155,810 · $194,410 | P10–P25 | below I–I | 1 | below I | O*NET 15-2051.01 Business Intelligence Analysts lists 'Business Intelligence Analyst (BI Analyst)' (record) |
| 15-1211 | Computer Systems Analysts | $63,160 · $80,900 · $103,790 · $132,360 · $166,030 | P10–P25 | below I–I | 1 | below I | BI roles that configure reporting systems are often filed as Computer Systems Analysts (your-input) |
| 15-1243 | Database Architects | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P0–P10 | below I | 1 | below I | BI developer/engineer roles that own warehouse models (your-input) |

### C — Data Engineer · floor $105,000 · family `data-engineer`

| SOC | Occupation (OEWS) | P10 · P25 · P50 · P75 · P90 | Floor percentile | Level now | Entries now | Level if DOL proposal took effect | Why plausible |
|---|---|---|---|---|---|---|---|
| 15-1243 | Database Architects | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P10–P25 | below I–I | 1 | below I | O*NET 15-1243.00 / 15-1243.01 list 'Big Data Engineer' (record) |
| 15-1242 | Database Administrators | $56,820 · $76,100 · $104,620 · $132,850 · $160,890 | P50–P75 | III–IV | 3–4 | I–III | O*NET 15-1242.00 Database Administrators lists 'Data Engineer' (record) |
| 15-1252 | Software Developers | $79,850 · $103,050 · $133,080 · $169,000 · $211,450 | P25–P50 | I–II | 1–2 | below I–I | data-platform engineering roles are often filed as Software Developers (your-input) |

## Offers and scenarios you entered

| Scenario | Title | Worksite | Base | Lottery read | Entries | Status | Next action |
|---|---|---|---|---|---|---|---|
| A (hypothetical) | Data Analyst | Chicago, IL | $85,000 | SOC-SENSITIVE | 1–4 | ASSESSED | before negotiating, ask the recruiter which SOC code and wage level the LCA will use; the answer decides 1 vs 2+ entries. Under at least one plausible SOC this wage may sit below the Level I prevailing wage: the employer could then register only with an acceptable alternative wage survey, and the registration counts once |
| B (hypothetical) | Business Intelligence Analyst | Boston, MA | $72,000 | LEVEL-I-AT-BEST | 1 | ASSESSED | at most 1 entry at this floor; negotiate above the next percentile point, or weigh the single-entry odds. Under at least one plausible SOC this wage may sit below the Level I prevailing wage: the employer could then register only with an acceptable alternative wage survey, and the registration counts once |
| C (hypothetical) | Data Engineer | New York, NY | $105,000 | SOC-SENSITIVE | 1–4 | ASSESSED | before negotiating, ask the recruiter which SOC code and wage level the LCA will use; the answer decides 1 vs 2+ entries. Under at least one plausible SOC this wage may sit below the Level I prevailing wage: the employer could then register only with an acceptable alternative wage survey, and the registration counts once |
| D (hypothetical) | Product Analyst | Chicago, IL | $90,000 | — | — | MANUAL-CHECK: title-not-in-soc-map (G3: add a family or skip) | add a title family to soc-map.json with its plausible SOC codes, or skip the role |

## Needs a human look

_Nothing._

## What this report cannot tell you

- **The real wage step.** The ladder used here is the *national* one from May 2024. The government's table for your worksite (July 2026 – June 2027, built on May 2025 data) is not in the repo. In expensive cities local wages run higher, so these steps are likely **too generous** there.
- **The job code.** The employer's immigration lawyer chooses it after the offer. The codes listed are the plausible ones a human approved, not the one that will be filed.
- **Your odds.** Entries are not odds; no published count of the registration pool by step was found.
- **Pay you will be offered.** A posted range is not an offer. The floor is used because an offer can land there.
- **Company median salary** in the sponsorship data covers *all* sponsored titles (mostly software engineers). It is shown for context and never compared with a data-role posting.

## Human gate G4

- [ ] I read every `parsed-text` quote below and it matches the posting.
- [ ] I checked the plausible job codes for each family (gate G3) before trusting any read.
- Signed: ______________________ Date: __________

## Run record

- Recipe `data-lottery-weight` v0.1.0 · as_of 2026-10-19 · board mode snapshot
- Persona `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json` (fictional: True) · SOC map `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json` (confirmed by: Akshit Verma (G3, 2026-10-19) — confirmed all four families as drafted, after run-1)
- Wage ladder `data/bls/oesm24nat/national_M2024_dl.xlsx (BLS OEWS May 2024, national, detailed occupations)` · sponsorship `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` · scorer `scripts/score/role-scorer.mjs`
- Audit: boards fetched 16 (unresolved 0) · postings on boards 1264 · data-titled 20 · excluded senior/intern/contract 14 · excluded non-US 3 · entry-eligible US 3
- Skip before the scorer: 17/20 data-titled postings dropped by the title and location rules (the scorer's own skip rate counts only what reached it)
- Scorer inputs: sponsorship (record), liveness (record), timeline (your-input). Fit is NOT scored, so each composite is sponsorship alone (tier p × 0.35 × gates); a Proven sponsor scores 0.315, just over the 0.30 Apply threshold, and a Likely sponsor (0.21) cannot reach Apply without a fit score
- Scorer timeline factor 1.0 (slack 90 days; factor = min(1, (opt_start + ceiling − max(as_of + lag, opt_start)) / ceiling))

### Parsed-text pay quotes (verify at G4)

- **SIGMA COMPUTING INC — Data Engineer (New York City, NY)**: "…tronomer, Airflow, Dagster) Advanced knowledge of working with public clouds (e.g., AWS, GCP) Additional Job details The base salary range for this position is $140k - $180k annually. Compensation may vary outside of this range depending on a number of…"
- **SIGMA COMPUTING INC — Data Engineer (San Francisco, CA)**: "…tronomer, Airflow, Dagster) Advanced knowledge of working with public clouds (e.g., AWS, GCP) Additional Job details The base salary range for this position is $140k - $180k annually. Compensation may vary outside of this range depending on a number of…"
