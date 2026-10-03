# Worked run — preopt-data-network-targets v0.1.1

## Executive summary

On 2026-10-03 the prototype ran end to end for a fictional pre-OPT MSIS student.
It read the shipped 80 Days CSV, the four Form D samples and the BLS compact
file, fetched 16 human-confirmed ATS boards live, and handed the evidence to the
existing scorer.

- **run-1 (live, v0.1.0):** APPLY-TAILOR 3 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 12.
- **What went wrong:** reading run-1 exposed a false positive. Zoox's only
  "live" data postings were part-time contract student jobs.
- **run-2 (v0.1.1, an offline replay of run-1's snapshot)** fixed it:
  APPLY-TAILOR 2 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 13.
- **Cross-checks:** values were checked by hand against the CSV, the APPLY-TAILOR
  postings were confirmed active by the repo's own Playwright checker, and four
  failure cases plus a live break attempt behaved as specified.
- **Final list:** one NETWORK target (Outset Medical), two applications to tailor
  (Klaviyo, Sigma Computing).

Who ran what: the commands below were executed by the AI agent (Claude Code) in
my session, at my direction. I confirmed the boards (G1) and signed G3. I
re-run from a clean checkout in `TEST-REPORT.md`.

## Inputs

| Input | Value | Label |
|---|---|---|
| Persona | Jack Spencer (fictional), MSIS, F-1 pre-OPT, Chicago — `scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json` | your-input |
| Graduation / OPT start / OPT end | 2026-12 / 2027-01-23 / 2028-01-22 | your-input |
| Unemployment ceiling, hiring lag, funding window | 90 days, 60 days (assumption), 24 months | your-input |
| Target titles / SOC | data analyst/engineer, analytics engineer, BI, ETL, data warehous* / 15-2051.01, 15-1243.01 | your-input |
| Board map | `boards.json`, 16 entries. Slugs proposed by the AI agent, all confirmed by me (G1) | your-input |
| Data | `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv`; `data/sec/form-d/processed/sample/*.sample.json` (4 samples, 50 companies each); `data/bls/compact/soc_occupation_compact.csv` | record |
| Live hosts called | `boards-api.greenhouse.io`, `api.lever.co`, `api.ashbyhq.com` (one GET per confirmed board) | — |

## Commands and real output

### 0. Engine baseline (assignment "before you start")

```text
$ npm run score -- data/examples/ch11-roles.json --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/engine-baseline

> the-reallocation-engine@1.0.0 score
> node scripts/score/role-scorer.mjs data/examples/ch11-roles.json --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/engine-baseline

✓ scored 5 roles → Apply 2 · Consider 1 · Skip 2 (skip 40%)
  course\2026fa\submissions\AkshitVerma-AV\runs\engine-baseline\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\runs\engine-baseline\role-scores.md
[exit 0]

$ npm run ats:scan -- --dry-run

> the-reallocation-engine@1.0.0 ats:scan
> node scripts/ats/scan.mjs --dry-run

Error: portals.yml not found. Run onboarding first.
[exit 1]
```

`ats:scan` fails on a fresh clone because `data/ats/` is gitignored and only
`portals.example.yml` ships. My prototype doesn't depend on it.

### 1. run-1 — live (v0.1.0)

```text
$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --live --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/run-1
✓ scored 16 roles → Apply 3 · Consider 0 · Skip 13 (skip 81%)
  course\2026fa\submissions\AkshitVerma-AV\runs\run-1\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\runs\run-1\role-scores.md
✓ 123 candidates → APPLY-TAILOR 3 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 12 (network-blocked 12)
  course\2026fa\submissions\AkshitVerma-AV\runs\run-1\network-targets.json  +  network-targets.md
exit 0
```

Board snapshot `fetched_at`: `2026-10-03T22:10:42+00:00`. run-1's Zoox APPLY-TAILOR
rested on these three matched postings. This is an excerpt of
`runs/run-1/network-targets.json`, reformatted as `title | location` (not terminal output):

```text
Contract  Student Worker - Data Analyst (Part-time) | Foster City, CA
Contract Student Worker - Autonomy Safety Data Engineer | Foster City, CA
Contract Student Worker - Data Analyst (20 hrs/wk) | Seattle, WA
```

### 2. Replay of run-1 offline (v0.1.0): reproducibility

```text
$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json --as-of 2026-10-03 --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/replay
✓ scored 16 roles → Apply 3 · Consider 0 · Skip 13 (skip 81%)
  course\2026fa\submissions\AkshitVerma-AV\runs\replay\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\runs\replay\role-scores.md
✓ 123 candidates → APPLY-TAILOR 3 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 12 (network-blocked 12)
  course\2026fa\submissions\AkshitVerma-AV\runs\replay\network-targets.json  +  network-targets.md
```

A separate comparison script (an inline `python -c` that loads both
`network-targets.json` files and compares each company's bucket and the counts)
printed:

```text
identical buckets: True counts equal: True
```

### 3. run-2 — v0.1.1 (contract / student-worker / part-time excluded; senior-only flag), replaying run-1's snapshot

```text
$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json --as-of 2026-10-03 --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/run-2
✓ scored 16 roles → Apply 2 · Consider 0 · Skip 14 (skip 88%)
  course\2026fa\submissions\AkshitVerma-AV\runs\run-2\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\runs\run-2\role-scores.md
✓ 123 candidates → APPLY-TAILOR 2 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 13 (network-blocked 13)
  course\2026fa\submissions\AkshitVerma-AV\runs\run-2\network-targets.json  +  network-targets.md
exit 0
```

The same kind of comparison script, run-1 against run-2, printed every company
whose bucket changed:

```text
CHANGED ZOOX INC APPLY-TAILOR -> SKIP | network-blocked: funding stale
```

The NETWORK and APPLY-TAILOR tables from `runs/run-2/network-targets.md`, pasted:

| Company | Sponsorship | Sponsored data titles | Board | Funding | Scorer | Next action |
|---|---|---|---|---|---|---|
| OUTSET MEDICAL INC (CA) | Likely [your-input rule] · 44 appr / 95.65% [record] · ⚠ senior-only data-title evidence | Staff Data Engineer [record] | none: 0 entry-eligible US data postings of 30 [record] | recent (CSV 2025-01-03; Form D not-in-sample) [record] | 0 ((0.6·0.35) × 0 × 1 = 0.000) | find one data-team employee or alum for a 20-min informational interview; re-check board in 14 days (the 3) |

| Company | Sponsorship | Scorer | Matched postings [record] |
|---|---|---|---|
| KLAVIYO INC | Proven [your-input rule] · 154 appr / 97.47% [record] | Apply — 0.315 ((0.9·0.35) × 1 × 1 = 0.315) | Analytics Engineer — Boston, MA https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003 |
| SIGMA COMPUTING INC | Proven [your-input rule] · 136 appr / 100.0% [record] · ⚠ senior-only data-title evidence | Apply — 0.315 ((0.9·0.35) × 1 × 1 = 0.315) | Data Engineer — New York City, NY https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003<br>Data Engineer — San Francisco, CA https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003 |

The 13 network-blocked sponsors (Pinterest, Zoox, Roku, Upstart, Gusto, Moloco,
Ginkgo, ZoomInfo, Coursera, NerdWallet, Socure, Cherre, Omada) are listed in full in
`runs/run-2/network-targets.md` § "SKIP — network-blocked by funding data".

### 4. Offline test

```text
$ python -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets -p "test_*.py" -v
test_expired_opt_stops_at_g0_and_writes_nothing (test_network_targets.FailureCases.test_expired_opt_stops_at_g0_and_writes_nothing) ... ok
test_out_dir_inside_repo_outside_namespace_is_refused (test_network_targets.FailureCases.test_out_dir_inside_repo_outside_namespace_is_refused) ... ok
test_requires_live_or_snapshot (test_network_targets.FailureCases.test_requires_live_or_snapshot) ... ok
test_soc_with_no_row_is_missing_not_invented (test_network_targets.FailureCases.test_soc_with_no_row_is_missing_not_invented) ... ok
test_stale_snapshot_stops_at_g2 (test_network_targets.FailureCases.test_stale_snapshot_stops_at_g2) ... ok
test_404_is_unresolved (test_network_targets.HappyPath.test_404_is_unresolved) ... ok
test_buckets (test_network_targets.HappyPath.test_buckets) ... ok
test_company_not_in_csv_is_never_scored (test_network_targets.HappyPath.test_company_not_in_csv_is_never_scored) ... ok
test_contract_student_worker_posting_does_not_count_as_live (test_network_targets.HappyPath.test_contract_student_worker_posting_does_not_count_as_live) ... ok
test_empty_board_is_unresolved_not_none (test_network_targets.HappyPath.test_empty_board_is_unresolved_not_none) ... ok
test_every_candidate_in_exactly_one_bucket (test_network_targets.HappyPath.test_every_candidate_in_exactly_one_bucket) ... ok
test_existing_scorer_was_called (test_network_targets.HappyPath.test_existing_scorer_was_called) ... ok
test_exit_zero_and_both_outputs (test_network_targets.HappyPath.test_exit_zero_and_both_outputs) ... ok
test_funding_requirement_blocks_and_is_reported (test_network_targets.HappyPath.test_funding_requirement_blocks_and_is_reported) ... ok
test_markdown_report_has_labels_and_sign_off (test_network_targets.HappyPath.test_markdown_report_has_labels_and_sign_off) ... ok
test_no_phone_numbers_in_outputs (test_network_targets.HappyPath.test_no_phone_numbers_in_outputs) ... ok
test_senior_intern_and_non_us_postings_do_not_count_as_live (test_network_targets.HappyPath.test_senior_intern_and_non_us_postings_do_not_count_as_live) ... ok
test_senior_only_evidence_is_flagged_not_bucketed (test_network_targets.HappyPath.test_senior_only_evidence_is_flagged_not_bucketed) ... ok
test_sponsorship_values_match_csv (test_network_targets.HappyPath.test_sponsorship_values_match_csv) ... ok
test_unresolved_never_sent_to_scorer (test_network_targets.HappyPath.test_unresolved_never_sent_to_scorer) ... ok
test_values_carry_source_labels (test_network_targets.HappyPath.test_values_carry_source_labels) ... ok
test_borderline_title_matches (test_network_targets.TitlePatterns.test_borderline_title_matches) ... ok
test_known_false_negative_is_still_missed (test_network_targets.TitlePatterns.test_known_false_negative_is_still_missed) ... ok
test_true_negatives (test_network_targets.TitlePatterns.test_true_negatives) ... ok
test_true_positives (test_network_targets.TitlePatterns.test_true_positives) ... ok

----------------------------------------------------------------------
Ran 25 tests in 2.739s

OK
```

### 5. Failure cases and deliberate break attempts

```text
$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-expired-opt.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json --as-of 2026-10-03 --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/should-not-exist
✗ G0 failed: opt_end_date 2026-05-31 is not after as_of 2026-10-03 — OPT window already closed
[exit 3]

ls: cannot access 'course/2026fa/submissions/AkshitVerma-AV/runs/should-not-exist': No such file or directory

$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json --as-of 2026-10-20 --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/should-not-exist
✗ G2 failed: snapshot fetched 2026-10-03 is 17 days before as_of 2026-10-20 (max 7)
[exit 5]

$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json --as-of 2026-10-03 --out-dir data/examples
✗ --out-dir data/examples is inside the repo but outside this contribution's namespaces ('course/2026fa/submissions/AkshitVerma-AV/', 'scripts/contrib/2026fa/AkshitVerma-AV-')
[exit 2]

$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --as-of 2026-10-03 --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/should-not-exist
✗ pass --live (network) or --snapshot <board-snapshot.json> (offline)
[exit 2]
```

**Break attempt: moved-ATS false target.** I pointed Klaviyo at its *empty* Ashby
board (a scratch copy of the board map, output to scratch, live call to
`api.ashbyhq.com`). If the rule were broken, the 0 postings would read as "no
openings", and Klaviyo, which has a live Analytics Engineer posting on
Greenhouse, would be turned away from applying.

```text
$ python scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards <scratch>/boards-break-klaviyo-ashby.json --live --out-dir <scratch>/break-klaviyo
! no company reached the scorer (no confirmed board returned live/none) — everything is MANUAL-CHECK
✓ 123 candidates → APPLY-TAILOR 0 · NETWORK 0 · MANUAL-CHECK 123 · SKIP 0 (network-blocked 0)
  ..\..\..\..\AKSHIT~1\AppData\Local\Temp\claude\c--Users-Akshit-Verma-PromptEngr-Assignment-1\2891bb55-8d21-4765-ac4d-9fdc5556c22d\scratchpad\break-klaviyo\network-targets.json  +  network-targets.md
[exit 0]
KLAVIYO -> MANUAL-CHECK | board returned zero postings total (likely moved ATS) — not evidence of no openings | http 200 | total 0
roles.json: []
```

### 6. Independent liveness cross-check (the repo's own Playwright checker)

First attempt, on one URL, before Playwright's browser was installed:

```text
$ npm run ats:liveness -- https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003

> the-reallocation-engine@1.0.0 ats:liveness
> node scripts/ats/check-liveness.mjs https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003

Checking 1 URL(s)...

Fatal: browserType.launch: Executable doesn't exist at C:\Users\Akshit Verma\AppData\Local\ms-playwright\chromium_headless_shell-1234\chrome-headless-shell-win64\chrome-headless-shell.exe
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
[exit 1]
```

Then `npx playwright install chromium`, then all three APPLY-TAILOR URLs:

```text
$ npm run ats:liveness -- https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003 https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003 "https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003"

> the-reallocation-engine@1.0.0 ats:liveness
> node scripts/ats/check-liveness.mjs https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003 https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003 https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003

Checking 3 URL(s)...

✅ active     https://job-boards.greenhouse.io/sigmacomputing/jobs/7809974003
✅ active     https://job-boards.greenhouse.io/sigmacomputing/jobs/7809973003
✅ active     https://www.klaviyo.com/careers/jobs/7737707003?gh_jid=7737707003

Results: 3 active  0 expired  0 uncertain
[exit 0]
```

## Verified vs. inferred (run-2), line by line

Outset Medical (the NETWORK target), then the run-level values:

| Value | Label | Where it came from |
|---|---|---|
| `OUTSET MEDICAL INC`, state CA | record | CSV row |
| 44 approvals, 2 denials, 95.65% approval rate | record | CSV `Total Approvals`, `Total Denials`, `Approval_Rate` (hand-checked below) |
| Sponsored data title "Staff Data Engineer" | record | CSV `top_job_titles_sponsored` |
| Tier **Likely**, p = 0.60 | your-input | My tier rule applied to the record (Ch.7 does not pin thresholds) |
| ⚠ senior-only data-title evidence | record + your-input | The title is a record; "senior" is decided by my excluded-title patterns |
| Funding date 2025-01-03 → `recent` | record + your-input | CSV `latest_funding_date`; the 24-month window is mine |
| Form D `not-in-sample` | record | No match in the 4 sample files. That's absence, not "unfunded" |
| Board: HTTP 200, 30 postings, 0 entry-eligible US data postings → `none` | record | Greenhouse API at 2026-10-03T22:10:42Z, filtered by my your-input patterns |
| Board `outsetmedical` is Outset Medical | your-input | Slug proposed by the AI agent from the name; the board calls itself "Outset Medical"; I confirmed it (G1) |
| Liveness factor 0.0 | record | Derived from the board status |
| Timeline factor 1.0 (slack 90 days) | your-input | Persona dates plus the 60-day hiring-lag **assumption** |
| Scorer: `(0.6·0.35) × 0 × 1 = 0.000`, Skip, `gated: liveness` | record (scorer output) | `runs/run-2/role-scores.json` from `scripts/score/role-scorer.mjs` |
| Bucket NETWORK | your-input rule over the scorer's output | Gated by liveness only, Likely tier, recent funding |
| "Find one data-team employee…" next action | your-input | Fixed text per bucket from the recipe |
| National medians $112,590 (15-2051) / $135,980 (15-1243) | record | BLS compact. National, parent code, **not** Chicago and **not** a scorer input |
| **model-judgment** | — | **None.** The prototype makes no model calls. The AI agent's board-name proposals became your-input only after I confirmed them |

## Verification

1. **Hand cross-check against the source CSV.** These rows were printed straight
   from the CSV (not from my outputs):
   `KLAVIYO INC 154.0 4.0 97.46835443037976 2022-07-26 ['Business Intelligence Engineer', …]`
   and `OUTSET MEDICAL INC 44.0 2.0 95.65217391304348 2025-01-03 [… 'Staff Data Engineer']`.
   They match the report (154 / 97.47%, Proven; 44 / 95.65%, Likely). Funding
   cutoff = 2026-10-03 − 24 months = 2024-10-03, so Outset (2025-01-03) is recent,
   while Sigma (2024-04-05) and Klaviyo (2022-07-26) are stale. Both correct.
2. **Scorer arithmetic.** 0.9 × 0.35 = 0.315 ≥ 0.30 → Apply; 0.6 × 0.35 × 0 = 0 → gated
   Skip. Both match `role-scores.json`.
3. **Independent liveness.** `ats:liveness` (Playwright, a different method from
   my API read) reports all 3 APPLY-TAILOR URLs active.
4. **Reproducibility.** The offline replay of run-1 gave identical buckets for all 123.
5. **Break attempts.** Expired OPT, stale snapshot, writing over `data/examples`,
   no board source, and the empty-Ashby-board mapping all failed safe (§5).

## Reflection

**What worked.**
- Keeping `unresolved` out of the scorer, because the scorer treats a missing
  liveness value as 1.0. The Klaviyo break attempt shows why.
- The funding rule's cost is visible rather than hidden: 13 blocked sponsors are
  listed by name.
- The independent liveness check agreed with the API read.

**What the prototype got wrong.**
- **Zoox.** run-1 recommended tailoring an application to Zoox on three
  "Contract Student Worker" part-time postings. They passed the title pattern and
  none of my exclusions. I hadn't predicted this failure case: a posting of the
  right *title* but the wrong *kind* of job for a sponsored full-time hire. It
  is fixed in v0.1.1 and pinned by a test.

**What it missed or under-states.**
- **Senior-only evidence.** 53 of 123 candidates, including Outset Medical (my
  only NETWORK target) and Sigma Computing, count as data-role sponsors only
  through senior titles. The record says less about new-grad sponsorship than
  the tier suggests.
- **Most candidates are still unchecked.** 107 of 123 (87%) are MANUAL-CHECK,
  because the board map only covers the 16 I confirmed.
- **The funding rule leaves almost nothing.** It cut the list to one company,
  on the shipped data.
- **The seniority filter is persona-relative.** At G3 I (Akshit, as human
  reviewer) selected Outset Medical for outreach toward a senior data-engineering
  path. For the fictional new-grad persona, Outset's senior-only evidence is a
  warning; for an experienced candidate it's a match. The patterns
  live in the persona file, so the prototype supports both. The worked run only
  exercised the new-grad one.

**One concrete next improvement.**
- Add a `--suggest-boards` mode. It would probe name-derived slugs on the three
  named hosts and write `confirmed: false` entries for G1, so the 77 Proven/Likely
  MANUAL-CHECK companies become a list I can confirm in minutes instead of hand
  research. The longer-term fix is [TODO: DATA SOURCE] title-level LCA data.
  That would replace the top-N title list and remove the senior-only blind spot
  at the source.

## Attestation

- Recipe: preopt-data-network-targets v0.1.1
- By: Akshit Verma · 2026-10-03

### Tested

| Ran | Saw | Expected |
|---|---|---|
| run-1 `--live`, 16 confirmed boards | exit 0; 123 candidates → APPLY-TAILOR 3 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 12 | both outputs written; every candidate in one bucket |
| Offline replay of run-1's snapshot | identical buckets and counts | identical |
| run-2 (v0.1.1) on the same snapshot | only Zoox changed (APPLY-TAILOR → SKIP) | only postings matching the new exclusion change |
| `python -m unittest … -v` | 25 tests OK, network patched to fail | all pass offline |
| Hand check: Klaviyo and Outset CSV rows vs. report | values match | match |
| `npm run ats:liveness` on the 3 APPLY-TAILOR URLs | 3 active | active |
| **Break:** persona with OPT ended 2026-05-31 | exit 3, G0 message, no output dir | stop, write nothing |
| **Break:** snapshot replay 17 days later | exit 5, G2 message | refuse a stale snapshot |
| **Break:** `--out-dir data/examples` | exit 2, refused | never write over tracked files |
| **Break:** Klaviyo mapped to its empty Ashby board, live | MANUAL-CHECK "not evidence of no openings"; `roles.json` = [] | unresolved, never scored, never NETWORK |

### Did not test

- Any persona other than Jack Spencer, or another SOC group.
- Lever/Ashby name verification. Their APIs expose no board name, so G1 for
  NerdWallet, Socure, Zoox and Cherre rests on my confirmation alone.
- Whether a `live` posting is a ghost posting, or what experience it requires.
  Fit isn't scored.
- Postings in non-US locations missing from my exclusion list.
- Full Form D quarters (not shipped). Funding is checked on samples only.
- Runs on macOS/Linux. Only Windows 11, Python 3.12, Node 24.
- The 107 companies without a board in the map.

### Broke during testing, fixed

- `npm run verify` failed on the fresh Windows clone (CRLF line endings). Fixed by
  setting `core.autocrlf=false` and `core.eol=lf` locally (FRICTIONAL.md).
- Ashby API returned 403 without a `User-Agent`. The prototype now always sends
  one (`network_targets.py`, `USER_AGENT`).
- `UnicodeEncodeError` printing `✓` on the cp1252 console. `main()` now
  reconfigures stdout and stderr to UTF-8.
- A test mislabeled a real Zoox title as non-data. The label was fixed, and the
  regex was left unchanged (`test_borderline_title_matches`).
- Zoox false APPLY-TAILOR in run-1. Fixed with a contract/student-worker/part-time
  exclusion in the persona (v0.1.1) and a regression test.
- `ats:liveness` couldn't launch until `npx playwright install chromium`.
