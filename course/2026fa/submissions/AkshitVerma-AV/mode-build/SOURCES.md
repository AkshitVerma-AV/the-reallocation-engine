# Sources and AI use — data-lottery-weight

## Executive summary

This page lists where every outside fact in the mode came from, and how much I
checked each one. The repo's own data files are the evidence for counts and
wages. Policy facts come from public rule summaries, and I mark which ones I
read in full and which I only saw as search summaries. It also records what the
AI assistant did and what I decided.

## Repository data (record)

| Fact | File | Checked how |
|---|---|---|
| H-1B approvals, approval rate, top sponsored titles, company median salary | `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | re-read directly by `verify_runs.py` |
| National wage percentiles P10–P90 (May 2024) | `data/bls/oesm24nat/national_M2024_dl.xlsx` | P50 equals the compact CSV median for 7/7 SOCs |
| "Data Analyst" listed under 7 occupations; "Data Engineer" under 15-1242; "Big Data Engineer" under 15-1243 | `data/bls/compact/soc_occupation_compact.csv`, `alternate_titles_sample` | grep, 2026-10-19 (sample of up to 8 titles per occupation, so incomplete) |
| Posted pay, posting presence | public Greenhouse board API, fetched 2026-10-20T03:16:02Z | `npm run ats:liveness` + snapshot replay |

## Policy sources

| Claim used in the mode | Source | How I read it |
|---|---|---|
| Weighted selection: published 2025-12-29, effective 2026-02-27; Level I→1 … Level IV→4 entries; level = highest OEWS level the offered wage meets for the SOC and area | [Federal Register 2025-23853](https://www.federalregister.gov/documents/2025/12/29/2025-23853/weighted-selection-process-for-registrants-and-petitioners-seeking-to-file-cap-subject-h-1b) (90 FR 60864) · [Greenberg Traurig summary](https://www.gtlaw.com/en/insights/2026/2/uscis-finalizes-wage-weighted-h-1b-cap-selection-rule-effective-feb-27-2026) | GT Law page **fetched**, 2026-10-19. The Federal Register page served a bot check, so I did **not** read the rule text itself |
| Below-Level-I wages: registrable with "acceptable alternative wage source", "entered one time only" | [Greenberg Traurig summary](https://www.gtlaw.com/en/insights/2026/2/uscis-finalizes-wage-weighted-h-1b-cap-selection-rule-effective-feb-27-2026) | **fetched**; this corrected the mode (0 → 1 entry) |
| Multiple worksites: USCIS checks whether "the lowest applicable wage level" was used | same | **fetched** |
| FY2027 registration ran 2026-03-04 → 03-19; cap reached | [AILA featured issue](https://www.aila.org/library/featured-issue-fy2027-h-1b-cap-season) | search summary only |
| DOL proposal (published 2026-03-27) would move Levels I–IV from ~17/34/50/67 to 34/52/70/88; not final | [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/03/dol-targets-prevailing-wages-sweeping-increases-proposed-for-h1b-h1b1) · [Ogletree](https://ogletree.com/insights-resources/blog-posts/dol-proposed-rule-would-increase-wage-levels-for-h-1b-visas-perm-labor-certifications/) · [Duane Morris](https://blogs.duanemorris.com/immigrationlaw/2026/03/29/dol-proposes-significant-increases-to-prevailing-wage-levels-for-h-1b-and-perm-programs-what-employers-need-to-know/) | search summaries only; "no final rule found" as of 2026-10-19 |
| OFLC wage year 2026-07 → 2027-06 uses May 2025 OEWS | [DOL OFLC technical release notes](https://www.dol.gov/sites/dolgov/files/ETA/oflc/pdfs/FINAL-OEWS-Technical-Release-Notes-for-July-2026-Wage-Year.pdf) · [FLAG wage data downloads](https://www.flag.dol.gov/wage-data/wage-data-downloads) | search summaries only |
| No USCIS breakdown of registrations by wage level found | the searches above | absence of evidence, stated as such |

Background only, not used by the mode: USCIS guidance (October 2025) says
F-1 → H-1B change-of-status petitions inside the US are exempt from the
$100,000 proclamation fee ([Holland & Hart](https://www.hollandhart.com/game-changer-for-h-1b-filings-change-of-status-petitions-escape-100000-fee),
[National Law Review](https://natlawreview.com/article/update-new-100000-h-1b-fee-who-exempt-and-who-must-pay)).
These were search summaries only, and the litigation status was not checked.

**Before relying on any of this for a real decision:** read the rule text in
the Federal Register in a browser, and ask the employer's immigration counsel.
This mode is a triage tool, not legal advice.

## AI use

Claude Code (Opus 5.5) worked under my direction in one session on 2026-10-19.

| Claude Code did | I decided |
|---|---|
| proposed the mode angle (wage-weighted lottery) after reading my Assignment 1 recipe and the repo | accepted the angle; scope stays my MSIS data-role situation |
| wrote `lottery_weight.py`, the tests, `BROKEN-mutants.py`, `verify_runs.py` | — |
| drafted `soc-map.json` from O*NET records plus labeled additions | **G3:** confirmed all four families as drafted, after run-1 held |
| carried my 2026-10-03 board confirmations forward | **G1** (signed 2026-10-03) |
| ran every command on this page and pasted the output | how to handle PR #44 (leave it open; push only after I confirm) |
| drafted the recipe, card, justification, worked run, run log | **G4:** signed the run-4 report, 2026-10-19 |
| ran the web searches and the one page fetch above | — |
