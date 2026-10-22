# Worked run — data-lottery-weight v0.1.0

## Executive summary

**What this is.** The record of running the lottery-weight mode for real on
2026-10-19: what went in, the exact commands and their pasted output, what was
established by data and what was judged, how I checked the output, what broke,
and what I'd change.

**Why read it.** It is the evidence behind the recipe's `RUNNABLE-SAMPLE` claim.
Every number below came out of a command shown on this page.

**What it found.**
- On 16 human-confirmed company job boards (1,264 postings), 20 postings had a
  data title, and 3 were open, US-based and entry-eligible.
- Both Sigma Computing Data Engineer postings ($140k floor) reach at least the
  second wage step under every plausible job code.
- Klaviyo's Analytics Engineer floor ($112,000) can't be settled by the national
  data. It sits $590 under the Data Scientists median.
- Of four hypothetical offers I entered, a $85,000 Data Analyst offer ranges
  from 1 to 4 lottery entries depending only on the job code.
- The first live attempt crashed. The second held correctly at the job-code
  gate until I signed it. The replay check later caught a timezone bug and
  contact emails in stored data. Checking the rule text caught a wrong entry
  count for wages below Level I. All four are fixed and pinned by tests.

## Scenario and inputs

| Input | Value | Source label |
|---|---|---|
| Persona | Jack Spencer (fictional stand-in for my situation): MSIS, F-1, OPT 2027-01-23 → 2028-01-22, STEM-eligible (+24 months), hiring lag 60 days, unemployment ceiling 90 days | your-input · `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json` |
| Registration windows | FY2028 2027-03-01 · FY2029 2028-03-01 · FY2030 2029-03-01 · FY2031 2030-03-01, **all assumed** (FY2027 ran 2026-03-04 → 03-19) | your-input |
| Boards | 16 companies, `confirmed: true` by me on 2026-10-03 (G1), carried forward from my network-targets recipe | your-input · `boards.json` |
| SOC map | 4 title families; codes labeled `record` (O*NET lists the title) or `your-input`; drafted by Claude Code, **confirmed by me 2026-10-19 after run-1 (G3)** | `soc-map.json` |
| Offers | A Data Analyst $85,000 Chicago · B BI Analyst $72,000 Boston · C Data Engineer $105,000 New York · D Product Analyst $90,000 Chicago, all **hypothetical**, no company named | your-input · `fixtures/offers-scenario.json` |
| Data | 80 Days CSV (30,369 rows; 1,557 with H-1B fields) · national OEWS May 2024 xlsx · O*NET compact CSV | record |

No private data was read. Nothing from `private/` or `data/ats/` was used.

## Run history (every run is kept under `runs/`)

| Run | What | Result |
|---|---|---|
| `engine-baseline/` | existing engine commands on a fresh clone | verify ✓ · doctor ✓ · liveness 3 active + 1 fabricated expired · scorer example ✓ · `bls:local-wage` exit 2 |
| `run-0-crash/` | first live run | **crashed**: Windows cp1252 console can't print the scorer's `✓` (kept as evidence) |
| `run-1/` | live, SOC map unconfirmed | **G3 held**: 3 postings + 3 offers `MANUAL-CHECK soc-map-not-confirmed`; Product Analyst `title-not-in-soc-map` |
| `run-2/` | live, after my G3 sign-off | first bracketed result: same reads as run-4; its offer entry counts predate the below-Level-I fix (0 instead of 1) |
| `run-3-replay/` | snapshot replay of run-2 | **caught two defects**: a UTC-vs-local date bug (refused with "−1 days"), then `pii-scan` found HR emails in stored posting text |
| `run-4-live/` | **final live run, code frozen** | 3 bracketed (2 CLEARS-LEVEL-II, 1 BRACKET-UNRESOLVED), offers 3 bracketed + 1 manual |
| `run-5-replay/` | snapshot replay of run-4 | decisions identical to run-4 |

## Commands and real output

### 1. The engine itself, on a fresh clone (`git clone -c core.autocrlf=false`, `npm install`)

```
$ npm run verify

> the-reallocation-engine@1.0.0 verify
> node scripts/conformance.mjs && node scripts/manifest-check.mjs

conformance: 158 files (85 md · 36 py · 30 js · 4 sh · 3 json)
✓ all conform (machine half of P4). Adequacy is still the human gate.
MANIFEST CHECK — The Reallocation Engine
==========================================

WARN (3):
  W1 ignore path not in .gitignore: archive/
  W2 private path not gitignored (PII/secret risk): private/
  W2 private path not gitignored (PII/secret risk): data/ats/

✓ manifest check passed (3 warnings)
[exit 0]
```

Doctor, trimmed to its verdict sections (full output in `runs/engine-baseline/doctor.txt`):

```
$ npm run doctor
...
PRIVACY (no personal data committed)
  ✓ no private/PII paths are tracked
...
SUMMARY
  environment: ✓ runnable
  recipes: 33/33 carry lifecycle frontmatter — all tracked
  next: continue
[exit 0]
```

Posting liveness. The fourth URL is a job ID I made up, as a deliberate break attempt:

```
$ npm run ats:liveness -- https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003 https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003 https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003 https://job-boards.greenhouse.io/sigmacomputing/jobs/1000000001

> the-reallocation-engine@1.0.0 ats:liveness
> node scripts/ats/check-liveness.mjs https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003 https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003 https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003 https://job-boards.greenhouse.io/sigmacomputing/jobs/1000000001

Checking 4 URL(s)...

✅ active     https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003
✅ active     https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003
✅ active     https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003
❌ expired    https://job-boards.greenhouse.io/sigmacomputing/jobs/1000000001
           redirect to https://job-boards.greenhouse.io/sigmacomputing?error=true

Results: 3 active  1 expired  0 uncertain
[exit 1]
```

The metro wage layer I wanted to use, and why the mode uses the national ladder instead:

```
$ npm run bls:local-wage -- --metro "Boston-Cambridge-Nashua, MA-NH" --soc 15-2051

> the-reallocation-engine@1.0.0 bls:local-wage
> python3 scripts/bls/local-wage-adjustment.py --metro Boston-Cambridge-Nashua, MA-NH --soc 15-2051

missing .venv � create it with:
  python3.13 -m venv .venv
  .venv/bin/pip install -r data/bls/local-wage/requirements.txt
[exit 2]
```

Two separate blockers. The script only looks for a POSIX `.venv/bin/python`,
and `data/bls/local-wage/` (metro OEWS, BEA RPP, crosswalk) isn't on `main` at
all. Both are TODOs 3 and 4 in the recipe.

The scorer on its shipped example, to confirm it runs before my mode calls it:

```
$ npm run score -- data/examples/ch11-roles.json --out-dir "$SCRATCH"

> the-reallocation-engine@1.0.0 score
> node scripts/score/role-scorer.mjs data/examples/ch11-roles.json --out-dir <scratch>/ch11

✓ scored 5 roles → Apply 2 · Consider 1 · Skip 2 (skip 40%)
  <scratch>\ch11\role-scores.json  +  <scratch>\ch11\role-scores.md
[exit 0]
```

### 2. run-1: the gate held

```
$ python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/lottery_weight.py --persona scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json --soc-map scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json --boards scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/boards.json --live --offers scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/offers-scenario.json --out-dir course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/run-1
✓ scored 3 roles → Apply 3 · Consider 0 · Skip 0 (skip 0%)
  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-1\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-1\role-scores.md
✓ G0 3 reachable lottery window(s) · 0 entry-eligible US posting(s):  · MANUAL-CHECK 3 · offers 4
  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-1\lottery-weight.json  +  lottery-weight.md
[exit 0]
```

The report (`runs/run-1/lottery-weight.md`) listed every row as
`MANUAL-CHECK: soc-map-not-confirmed (G3: family '…' awaits a human)`. The
summary line above says "0 entry-eligible" when it meant "0 bracketed" (3 were
eligible). That was a wording bug in my script, fixed before run-2. I then read
`soc-map.json` and signed G3:
`"confirmed_by": "Akshit Verma (G3, 2026-10-19) — confirmed all four families as drafted, after run-1"`.

### 3. run-4: the final live run (code frozen)

```
$ python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/lottery_weight.py --persona scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json --soc-map scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json --boards scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/boards.json --live --offers scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/offers-scenario.json --out-dir course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/run-4-live
✓ scored 3 roles → Apply 3 · Consider 0 · Skip 0 (skip 0%)
  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-4-live\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-4-live\role-scores.md
✓ G0 3 reachable lottery window(s) · 3 entry-eligible US posting(s) of 20 data-titled · bracketed 3 (BRACKET-UNRESOLVED 1 · CLEARS-LEVEL-II 2) · MANUAL-CHECK 0 · offers 4 (bracketed 3)
  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-4-live\lottery-weight.json  +  lottery-weight.md
[exit 0]
```

Board fetch time: `"fetched_at": "2026-10-20T03:16:02+00:00"` (23:16 EDT, 2026-10-19).
From `runs/run-4-live/lottery-weight.md`, pasted:

| Company | Posting | Location | Posted base (source) | Lottery read (floor, every plausible SOC) | Entries at floor | Scorer | Next action |
|---|---|---|---|---|---|---|---|
| KLAVIYO INC | [Analytics Engineer](https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003) | Boston, MA | $112,000–$168,000 (structured) | **BRACKET-UNRESOLVED** | 1–2 | Apply (0.315) | the national ladder cannot settle the level; check the OFLC wage table for the worksite before negotiating |
| SIGMA COMPUTING INC | [Data Engineer](https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003) | New York City, NY | $140,000–$180,000 (parsed-text) | **CLEARS-LEVEL-II** | 3–4 | Apply (0.315) | apply/tailor if the scorer agrees; the floor already earns 2+ entries under every plausible SOC (national proxy) |
| SIGMA COMPUTING INC | [Data Engineer](https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003) | San Francisco, CA | $140,000–$180,000 (parsed-text) | **CLEARS-LEVEL-II** | 3–4 | Apply (0.315) | apply/tailor if the scorer agrees; the floor already earns 2+ entries under every plausible SOC (national proxy) |

Two of the per-SOC tables, excerpted. Header rows are dropped, Klaviyo's "why
plausible" text is shortened to "...", and "Market Research Analysts" is short
for "Market Research Analysts and Marketing Specialists". The full tables are in
the report.

```
### KLAVIYO INC — Analytics Engineer · floor $112,000 / ceiling $168,000 · family `analytics-engineer`
| 15-2051 | Data Scientists     | $63,650 · $82,630 · $112,590 · $155,810 · $194,410 | P25–P50 | I–II | 1–2 | below I–I | ... (your-input) |
| 15-1243 | Database Architects | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P25–P50 | I–II | 1–2 | below I–I | ... (your-input) |
| 15-1252 | Software Developers | $79,850 · $103,050 · $133,080 · $169,000 · $211,450 | P25–P50 | I–II | 1–2 | below I–I | ... (your-input) |

### A — Data Analyst · floor $85,000 · family `data-analyst`
| 15-2051 | Data Scientists          | $63,650 · $82,630 · $112,590 · $155,810 · $194,410 | P25–P50 | I–II      | 1–2 | below I–I | O*NET 15-2051.00 Data Scientists lists 'Data Analyst' (record) |
| 15-2041 | Statisticians            | $60,390 · $79,210 · $103,300 · $137,610 · $170,700 | P25–P50 | I–II      | 1–2 | below I–I | O*NET 15-2041.00 Statisticians lists 'Data Analyst' (record) |
| 15-1243 | Database Architects      | $81,630 · $107,900 · $135,980 · $169,480 · $209,990 | P10–P25 | below I–I | 1   | below I   | O*NET 15-1243.00 Database Architects lists 'Data Analyst' (record) |
| 13-1161 | Market Research Analysts | $42,070 · $56,220 · $76,950 · $104,870 · $144,610 | P50–P75 | III–IV    | 3–4 | I–III     | marketing/growth data-analyst roles are often filed as Market Research Analysts (your-input) |
```

| Scenario | Title | Worksite | Base | Lottery read | Entries | Status |
|---|---|---|---|---|---|---|
| A (hypothetical) | Data Analyst | Chicago, IL | $85,000 | SOC-SENSITIVE | 1–4 | ASSESSED |
| B (hypothetical) | Business Intelligence Analyst | Boston, MA | $72,000 | LEVEL-I-AT-BEST | 1 | ASSESSED |
| C (hypothetical) | Data Engineer | New York, NY | $105,000 | SOC-SENSITIVE | 1–4 | ASSESSED |
| D (hypothetical) | Product Analyst | Chicago, IL | $90,000 | — | — | MANUAL-CHECK: title-not-in-soc-map (G3: add a family or skip) |

Audit line from the report: `boards fetched 16 (unresolved 0) · postings on boards 1264 · data-titled 20 · excluded senior/intern/contract 14 · excluded non-US 3 · entry-eligible US 3` and `Skip before the scorer: 17/20`.

### 4. run-5: replay of run-4's saved snapshot

```
$ python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/lottery_weight.py --persona scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json --soc-map scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json --boards scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/run-4-live/board-snapshot.json --as-of 2026-10-19 --offers scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/offers-scenario.json --out-dir course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/run-5-replay
✓ scored 3 roles → Apply 3 · Consider 0 · Skip 0 (skip 0%)
  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-5-replay\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-5-replay\role-scores.md
✓ G0 3 reachable lottery window(s) · 3 entry-eligible US posting(s) of 20 data-titled · bracketed 3 (BRACKET-UNRESOLVED 1 · CLEARS-LEVEL-II 2) · MANUAL-CHECK 0 · offers 4 (bracketed 3)
  course\2026fa\submissions\AkshitVerma-AV\mode-build\runs\run-5-replay\lottery-weight.json  +  lottery-weight.md
[exit 0]
```

## Verified vs inferred, line by line

| Claim in the run-4 report | Kind | Established by |
|---|---|---|
| 16 boards returned HTTP 200 with 1,264 postings; 20 data-titled; 3 entry-eligible US | **verified** (record at fetch time) | board APIs; counts in `audit`; reproduced by replay |
| The 3 postings were live | **verified** (record), twice | in the board API at fetch time **and** `npm run ats:liveness` (3 active) |
| Klaviyo AE pay $112,000–$168,000 | **verified** (record) | Greenhouse `pay_input_ranges` (structured) |
| Sigma DE pay $140,000–$180,000 | **verified, text-derived** | strict parse of the sentence "The base salary range for this position is $140k - $180k annually", quoted for G4 |
| Klaviyo 154 approvals / 97.47%; Sigma 136 / 100% → Proven | **verified** count; tier **rule is your-input** | 80 Days CSV, re-read directly by `verify_runs.py` |
| OEWS P10–P90 for each SOC | **verified** (record) | national xlsx; P50 equals the compact CSV median for all 7 SOCs |
| "$112,000 falls between P25 and P50 for 15-2051" | **verified** (arithmetic on record) | bracket function; 34 tests incl. exact-edge test |
| Level I ≈ P17, II ≈ P34, III ≈ P50, IV ≈ P67 | **inferred** (published approximation) | law-firm and DOL summaries (SOURCES.md); exact cut-offs need the OFLC table |
| Below the Level I proxy = 1 entry, only with an alternative wage survey | **inferred** from a rule summary | GT Law summary of 90 FR 60864 (the Federal Register page blocked automated reads) |
| "I–II" / "1–2 entries" | **inferred** from the two rows above | range, not a point; the mode never narrows it |
| Which SOCs are plausible per title | **record + human judgment** | O*NET alternate titles (record); 13-1161, 15-1211, 15-1252 and the whole analytics-engineer family are **my judgment** (your-input), signed at G3 |
| CLEARS-LEVEL-II / BRACKET-UNRESOLVED / SOC-SENSITIVE | **inferred** by a fixed rule (floor, worst case) | rule stated in the recipe; mutants 1–3 show the tests catch three specific deviations from it |
| National ladder is "likely too generous" in Boston/NYC/SF | **model judgment**, labeled | not checked locally (metro data missing) |
| 3 reachable lottery rounds | **inferred** from your-input dates | persona + **assumed** window dates; assumes an E-Verify employer |
| Scorer Apply 0.315 | **verified** arithmetic | `role-scores.json`; 0.90 × 0.35 × 1 × 1 by hand; fit **not scored** |
| Offer rows A–D | **your-input** amounts, **verified** brackets | hypothetical inputs; same ladder arithmetic |
| "Ask the recruiter which SOC…" | **drafted guidance** | fixed text per read; not a model output |

Nothing in this run was produced by asking an LLM to judge a posting. Claude
Code wrote the code, drafted the SOC map (which I then confirmed) and drafted this write-up.

## Verification: how I know the output is real

1. **Re-ran from the saved snapshot** (run-5). `verify_runs.py` confirms the
   decisions are identical across all 7 rows, and so are the audit counts:

```
$ python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/verify_runs.py course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/run-4-live course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/run-5-replay
1. live run-4-live vs replay run-5-replay decisions identical: True (7 rows)
   audit identical: True {'boards_fetched': 16, 'boards_unresolved': 0, 'postings_total': 1264, 'data_title_postings': 20, 'excluded_title_rule': 14, 'excluded_non_us': 3, 'entry_eligible_us': 3}
2. 13-1161 xlsx P50    76,950  compact-CSV median    76,950  match=True
2. 15-1211 xlsx P50   103,790  compact-CSV median   103,790  match=True
2. 15-1242 xlsx P50   104,620  compact-CSV median   104,620  match=True
2. 15-1243 xlsx P50   135,980  compact-CSV median   135,980  match=True
2. 15-1252 xlsx P50   133,080  compact-CSV median   133,080  match=True
2. 15-2041 xlsx P50   103,300  compact-CSV median   103,300  match=True
2. 15-2051 xlsx P50   112,590  compact-CSV median   112,590  match=True
3. KLAVIYO INC          approvals log=154 csv=154  rate log=97.47 csv=97.47  tier=Proven
3. SIGMA COMPUTING INC  approvals log=136 csv=136  rate log=100.0 csv=100.0  tier=Proven
3. SIGMA COMPUTING INC  approvals log=136 csv=136  rate log=100.0 csv=100.0  tier=Proven
4. KLAVIYO INC          composite 0.315  hand: 0.90*0.35*1.0*1.0 = 0.315  | (0.9·0.35) × 1 × 1 = 0.315
4. SIGMA COMPUTING INC  composite 0.315  hand: 0.90*0.35*1.0*1.0 = 0.315  | (0.9·0.35) × 1 × 1 = 0.315
4. SIGMA COMPUTING INC  composite 0.315  hand: 0.90*0.35*1.0*1.0 = 0.315  | (0.9·0.35) × 1 × 1 = 0.315
5. 'probability' key present: False | phone/executive columns present: False
[exit 0]
```

2. **Cross-checked a count against an independent source.** The xlsx parser
   (my own standard-library code) and the repo's compact CSV (built by
   `scripts/bls/extract-soc-occupation-table.py`) agree on all 7 medians.
3. **Two live fetches agree.** run-2 and run-4 were fetched about 18 minutes
   apart. Their reads, statuses and audit counts are identical. Offers A–C
   differ only in the lower entry bound (0 in run-2, 1 in run-4), because run-2
   predates the below-Level-I correction listed under "Broke during testing".
4. **Parsed the JSON**: `node scripts/conformance.mjs` → `45 files (29 json · 4 py · 12 md)`, `✓ all conform`.
5. **Tests** (offline; they read the real shipped OEWS file and call the real scorer):

```
$ python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight -p "test_*.py"
..................................
----------------------------------------------------------------------
Ran 34 tests in 5.091s

OK
[exit 0]
```

6. **Deliberately tried to break it.** I planted three plausible bugs in the
   real module, and the suite catches each one:

```
$ python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/BROKEN-mutants.py
KILLED    strict-edge (> not >=)             1 failing test(s): test_exactly_at_median_counts_as_reached
KILLED    interpolate a point estimate       8 failing test(s): test_112k_analytics_engineer_is_unresolved_not_guessed, test_85k_data_analyst_is_soc_sensitive, test_below_p10_is_below_level_one, test_between_p25_and_p50_is_one_or_two …
KILLED    read the ceiling, not the floor    2 failing test(s): test_confirmed_run_buckets_and_calls_real_scorer, test_read_uses_the_floor_not_the_ceiling
3/3 mutants killed
[exit 0]
```

   Then I made G0 refuse on purpose: a persona without STEM OPT, run on 2027-01-15:

```
$ python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/lottery_weight.py --persona scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-no-stem.json --soc-map scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json --offers scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/offers-scenario.json --as-of 2027-01-15 --out-dir course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/verification/g0-refusal-out
✗ G0 failed: no H-1B registration window is reachable before work authorization ends — the mode refuses to bracket wages for a lottery the persona cannot enter
[exit 3]
$ ls course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/verification/g0-refusal-out
ls: cannot access 'course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/verification/g0-refusal-out': No such file or directory
```

7. **Privacy:** `node scripts/pii-scan.mjs` → 1 finding: the maintainer address in
   a `package-lock.json` deprecation notice. That finding is already on `main`;
   this branch doesn't touch the file.

## Attestation

- Recipe: data-lottery-weight v0.1.0
- By: Akshit Verma (run with Claude Code) · 2026-10-19

### Tested

| Ran | Saw | Expected |
|---|---|---|
| `npm run verify`, `npm run doctor` on a fresh clone | exit 0 both; 158 files conform; 0 tracked private paths | the engine is runnable before I add anything |
| live run, SOC map unconfirmed (run-1) | 3 postings + 3 offers `MANUAL-CHECK soc-map-not-confirmed`; nothing bracketed | G3 is a hard stop, not a warning |
| live run after my G3 sign-off (run-4) | 20 data-titled → 3 eligible → 2 CLEARS-LEVEL-II, 1 BRACKET-UNRESOLVED; scorer Apply 0.315 × 3 | brackets for open entry postings, scorer called not copied |
| replay run-4's snapshot (run-5) + `verify_runs.py` | decisions and audit identical; P50 matches compact CSV ×7; sponsorship matches CSV; composite = hand arithmetic | deterministic, traceable output |
| `npm run ats:liveness` on the 3 postings + **one fabricated job ID** | 3 active, fabricated → expired (redirect `?error=true`) | liveness gate distinguishes real from dead |
| **break:** 3 mutants (`>` for `>=`, interpolation, ceiling-for-floor) | all killed (1, 8, 2 failing tests) | tests pin the edge rule, the no-guess rule and the conservative read |
| **break:** no-STEM persona, as_of 2027-01-15 | exit 3, no output directory created | timeline is a gate that writes nothing |
| **break:** stale snapshot, hourly pay, two ranges in text, CAD pay, inverted range, top-coded percentile, OEWS schema change, out-dir in `logs/` | each refused with its reason or exit code (unit tests) | refusal, never a guessed read |
| Product Analyst offer (no SOC family) | `MANUAL-CHECK title-not-in-soc-map` | unmapped titles are not forced into a family |
| `node scripts/pii-scan.mjs` after redaction | only the `main` lockfile finding | no contact data in the branch |
| G4: re-fetched both Sigma postings and searched for the quoted pay sentence, then signed the run-4 report | sentence present in both (True, True); signed Akshit Verma, 2026-10-19 | every parsed-text quote matches the live posting before release |

### Did not test

- **Real worksite prevailing wages.** No OFLC table, so no row was checked against
  a real Level I–IV dollar figure. The level mapping (17/34/50/67) is the published
  approximation, not OFLC's formula output.
- **Whether any employer actually files under the codes in `soc-map.json`.** No LCA
  disclosure data was used.
- **Lever and Ashby pay parsing on live data.** None of the 3 eligible postings
  were on Lever or Ashby. Those paths are covered only by synthetic unit-test inputs.
- **More than 16 boards.** 107 sponsor companies from my earlier recipe have no
  confirmed board, and this mode was not run on them.
- **A real offer for a real person.** All four offers are hypothetical.
- **macOS/Linux.** Every run was on Windows 11, Python 3.12.10, Node 24.19.0.
- **The scorer's own date.** `role-scores.md` is stamped 2026-10-20 (UTC) while my
  run is 2026-10-19 (local). That's in a maintained file, so it was noted, not patched.

### Broke during testing, fixed

- **Rule check, entry count:** v0.1.0 first mapped a wage below the Level I proxy to
  **0 entries** and told the student the employer "could not file". Reading the rule
  summary while writing SOURCES.md showed that a below-Level-I wage can still be
  registered with an acceptable alternative wage source, and is then entered once.
  Fix: `ENTRIES[0] = 1` with the `below_level_I_possible` flag and the corrected
  next-action text. `test_below_p10_is_below_level_one` now asserts 1 entry, and
  `test_85k_data_analyst_is_soc_sensitive` expects 1–4. Offer A went from 0–4 to
  1–4 entries.
- **run-0, crash:** `UnicodeEncodeError: 'charmap' codec can't encode character '✓'`
  when printing the scorer's output through a Windows pipe. Fix: `main()` reconfigures
  stdout/stderr to UTF-8 (`lottery_weight.py`, `BROKEN-mutants.py`).
- **run-1, wording:** the summary said "0 entry-eligible" when 3 were eligible and 0
  bracketed. Fix: the summary now reports eligible and bracketed separately.
- **run-3, timezone:** replaying run-2's snapshot on the same evening refused with
  "fetched 2026-10-20 is -1 days from as_of 2026-10-19". `fetched_at` is UTC and
  `as_of` is local. Fix: the fetch time is converted to local time before comparing.
  Regression test `test_late_evening_utc_fetch_is_not_a_future_snapshot`.
- **run-3, privacy:** `pii-scan` found HR contact emails (`…@Roku.com`, `…@zoox.com`)
  in stored posting text. Fix: `slim_posting()` redacts emails/phones with the same
  patterns as `pii-scan.mjs` and drops Greenhouse `blurb` HTML at fetch time. The
  three earlier snapshots were redacted after the fact with `redact_snapshot()`, and
  each carries a `"redacted"` field. A replay from the redacted run-2 snapshot made
  identical decisions, so the redaction removed nothing the mode reads.
- **Test design:** `test_g3_unconfirmed_brackets_nothing` used the shipped
  `soc-map.json` and failed once I signed G3. Fix: tests build their own confirmed or
  unconfirmed copy and never depend on a live gate's state.
- **Coverage gap:** the ceiling-for-floor mutant was first killed by only one
  end-to-end test. Added `test_read_uses_the_floor_not_the_ceiling`.
- **Report honesty:** the scorer note hard-coded "0.315 … clears by 0.015", which
  would be wrong for a Likely-tier sponsor. It now states the general rule. The
  "the government has not published…" lines became "no published count … was
  found", because a search was all I had. "entries Under" became "entries. Under".

## Reflection

**What went well.**
- The gates did their job on real data. G3 held the first live run, G0 refused
  a persona with no reachable round, and liveness rejected a fabricated job ID.
- The replay check found two defects that a single live run would have hidden:
  the timezone bug and the stored contact emails.
- The most useful output was not a score. It was one sentence a student can say
  to a recruiter: *"Which SOC code and wage level would the LCA use?"*

**What the mode got wrong or missed.**
- *I encoded a rule detail from memory before checking the text.* Wages below
  Level I were scored as 0 entries until I read the rule summary. Every test
  passed with the wrong rule, because tests check the code against my reading of
  the rule, not against the rule itself. Only the source check caught it.
- *The national ladder flatters high-cost metros.* All three real postings are in
  Boston, New York or San Francisco, exactly where the bias runs optimistic. Sigma's
  "CLEARS-LEVEL-II" could be Level II at the New York worksite rather than III–IV.
  Under the DOL proposal it would be I–III even nationally.
- *Thin sample.* Only 3 of 1,264 postings reached the wage check, and none was a
  Data Analyst role, which is the most SOC-sensitive title. The hypothetical offers
  carry that case.
- *My persona excludes "II".* `Data Engineer II` is often an early-career title.
  The exclusion is my input, and it may be dropping real targets.
- *The G0 refusal message is generic.* It doesn't say which window failed or why.
  The per-window reasons exist in the code but are only written to the JSON, which
  a refused run never writes.
- *Fit is unscored.* Every Apply is sponsorship alone, at 0.315 against a 0.30 threshold.

**Next steps, in order.**
1. Ingest the OFLC 2026–27 wage table (TODO 1) and re-run. Success means
   `BRACKET-UNRESOLVED` rows become single levels for each worksite.
2. Ingest LCA disclosure data (TODO 2) so G3 starts from what Klaviyo and Sigma
   actually filed for these titles.
3. Confirm boards for the 107 unmapped sponsors from my earlier recipe, starting
   with those whose top sponsored titles include "Data Analyst".
4. Print per-window reasons in the G0 refusal message.
5. Run on a real offer, kept in `private/`, before claiming RUNNABLE-LIVE.
