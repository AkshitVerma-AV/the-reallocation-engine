---
status: RUNNABLE-SAMPLE   # DRAFT | SPECIFIED | RUNNABLE-SAMPLE | RUNNABLE-LIVE | VERIFIED
todos_open: 6
last_gate: "G4 signed by Akshit Verma, 2026-10-19, on course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/run-4-live/lottery-weight.md (G3 signed 2026-10-19 after run-1 held; G1 carried forward from 2026-10-03); run log logs/runs/2026fa-AkshitVerma-AV-2.md"
attestation: null  # set only at VERIFIED. Fictional persona + hypothetical offers + one evening's live fetch of 16 boards.
recipe_version: 0.1.0
---

# data-lottery-weight — How Many Lottery Entries Could This Data Job's Pay Earn?

## Executive summary

**What it does.** Since the spring 2026 H-1B lottery, an employer's registration
gets more chances the higher the offered salary sits on the government's
four-step wage ladder: one entry at the bottom step, four at the top. This
mode takes data-analyst and data-engineer postings that are open today at
companies with a strong sponsorship record, reads the pay range each posting
publishes, and works out which steps that pay could reach, under every job code
the employer could plausibly file. It also takes offers a student types in.

**Who it is for.** An international MS Information Systems student on F-1 who
has not started OPT yet (graduating December, OPT starting late January) and is
aiming at Data Analyst, Business Intelligence, Analytics Engineer and Data
Engineer roles. The persona in this recipe is fictional (Jack Spencer,
`jack.spencer@example.com`).

**What it decided on its first real run.** Of 20 data-titled postings on 16
checked boards, 3 were open, US-based and entry-eligible. Two Sigma Computing
Data Engineer postings reach at least the second step under every plausible
code. Klaviyo's Analytics Engineer floor ($112,000) lands $590 under one code's
national median, so the national ladder cannot say whether it earns one entry or
two, and the mode says so rather than guessing. For a hypothetical $85,000 Data
Analyst offer, the plausible codes span 1 to 4 entries. The job code, which the
student never sees, decides the result.

**What it refuses to do.** It never prints a chance of winning, never
interpolates between published wage percentiles, never treats a company-wide
median salary as the pay for a data role, and never brackets a posting whose pay
it could not read.

Two readers: this file is for the agent. The card
`recipes/cases/2026fa/AkshitVerma-AV-data-lottery-weight.card.md` is for the person.

## Required reads

1. `SNICKERDOODLE.md` (prime directive, gates, attestation), `DOMAIN.md` → Known gaps #3 and #9.
2. `DATA_CONTRACT.md` §Zero-Conditions. The 80 Days CSV holds phone numbers and
   executive names; posting texts hold HR contact emails. Neither is copied into outputs.
3. `scripts/score/role-scorer.mjs`, the decision core this recipe calls (not copies).
   `role_quality` weight is 0.0, so wages never enter the composite.
4. `recipes/local-wage-adjustment.md`, the metro wage layer this recipe would use
   if its data were on `main` (it is not; see Proposed additions).
5. Federal Register 2025-23853 (weighted selection, 90 FR 60864) and the DOL
   prevailing-wage NPRM of 2026-03-27. Both are summarized in
   `course/2026fa/submissions/AkshitVerma-AV/mode-build/SOURCES.md`.

## Purpose

Use this mode **after** you have a list of postings or an offer, and **before**
you spend an application or start negotiating. It answers one question: *at the
pay this employer has published or offered, how many lottery entries could my
registration carry, and what would change that number?*

Use it when:

- you are on F-1/OPT and your H-1B would be cap-subject (not a university or
  nonprofit research employer), and
- you are choosing between data roles, or negotiating one, before the next
  registration window (offer accepted before the window opens).

Do not use it when you are cap-exempt, already selected, or comparing roles for
reasons other than lottery weight. It says nothing about fit, interview odds or
career value.

## Source inventory

| Source | Path / command | On a fresh clone? | Label of values it yields |
|---|---|---|---|
| Sponsorship history (80 Days) | `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` — columns kept: `company_name`, `state`, `Total Approvals`, `Total Denials`, `Approval_Rate`, `median_salary_offered`, `top_job_titles_sponsored` | yes | record |
| National OEWS wage ladder | `data/bls/oesm24nat/national_M2024_dl.xlsx`, sheet 1, `O_GROUP = detailed`, columns `A_PCT10 · A_PCT25 · A_MEDIAN · A_PCT75 · A_PCT90` (May 2024) | yes | record |
| O*NET alternate titles (SOC candidates) | `data/bls/compact/soc_occupation_compact.csv`, column `alternate_titles_sample` (up to 8 titles per occupation) | yes | record |
| Public ATS boards | `boards-api.greenhouse.io/v1/boards/<slug>/jobs` (+ `/jobs/<id>?pay_transparency=true`), `api.lever.co/v0/postings/<slug>?mode=json`, `api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true` | network | record, at fetch time |
| Board map (G1) | `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/boards.json` (16 entries, human-confirmed 2026-10-03) | yes | your-input |
| SOC map (G3) | `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json` (4 title families) | yes | record + your-input, per code |
| Persona (G0) | `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json` | yes | your-input |
| Offers (optional) | `--offers <file>`; worked run uses `fixtures/offers-scenario.json` (hypothetical) | yes | your-input |
| Role scorer | `npm run score` = `node scripts/score/role-scorer.mjs <roles.json> --out-dir <dir>` | yes | record / your-input per term |
| Posting liveness cross-check | `npm run ats:liveness -- <url> …` (Playwright; needs `npx playwright install chromium`) | needs Chromium | record |
| Metro wage (not used) | `npm run bls:local-wage -- --metro … --soc …` | **fails**: needs a POSIX `.venv/bin/python` and `data/bls/local-wage/*.csv`, which are not on `main` | — |

### Run commands (from the repo root)

```bash
# live: fetch the 16 confirmed boards, bracket open postings, plus your offers
python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/lottery_weight.py \
  --persona  scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/persona-jack-spencer.json \
  --soc-map  scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/soc-map.json \
  --boards   scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/boards.json \
  --live --offers scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/offers-scenario.json \
  --out-dir  course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/<run-name>

# offline replay of a saved fetch (within 7 days of the fetch): replace --live with
#   --snapshot <run-dir>/board-snapshot.json --as-of YYYY-MM-DD

# cross-check a live run against its replay, and against independent sources
python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/verify_runs.py <live-run-dir> <replay-run-dir>

# tests (offline) and break attempts
python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight -p "test_*.py"
python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/BROKEN-mutants.py
```

Standard library only (Python 3.12, Node 20+). Contribution tools get no
`package.json` script until a maintainer promotes them (CONTRIBUTING.md).

## Inputs

| Input | Who sets it | Notes |
|---|---|---|
| `opt_start_date`, `opt_end_date`, `stem_opt_eligible`, `stem_opt_months` | student | decide how many registration windows fall inside work authorization |
| `registration_windows[]` | student | FY2028 dates are not announced; `2027-03-01` is an assumption, flagged in every output |
| `hiring_lag_days` (60), `unemployment_ceiling_days` (90) | student | lag = how long from today until an accepted offer could exist |
| `target_title_patterns`, `exclude_posting_title_patterns`, `exclude_posting_location_patterns` | student | the persona excludes senior, `II/III/IV`, intern, contract and non-US postings; loosen `II` if you would take a Data Engineer II |
| `boards.json` | student (G1) | exact 80 Days `company_name` → ATS + slug, `confirmed: true` |
| `soc-map.json` | student (G3) | per title family: plausible SOC codes, each labeled `record` (O*NET lists the title there) or `your-input` (with a reason); `pruned` codes listed with reasons |
| offers file | student | `label`, `title`, `worksite`, `base_annual_usd`, `hypothetical` |

## The wage-ladder rule (closed DEFINE, with reasoning)

OEWS publishes five annual percentiles per occupation: P10, P25, P50, P75, P90.
The four wage levels sit near the 17th, 34th, 50th and 67th percentiles (the
DOL proposal would move them to 34/52/70/88). A wage's percentile is only known to lie between the two
published points around it, so the mode reports the **range of levels that
interval allows**:

```
q_lo = highest published percentile the wage reaches (0 if below P10)
q_hi = next published percentile above it          (100 if at/above P90)
level_min = #thresholds ≤ q_lo      level_max = #thresholds < q_hi
entries   = level (Level I = 1 … Level IV = 4); level 0 = below the Level I proxy → still 1 entry,
            but only if the employer has an acceptable alternative wage source (flagged)
```

Example: $85,000 against Data Scientists (P25 $82,630, P50 $112,590) gives
P25–P50, so Level I–II and 1–2 entries. Interpolating would give one confident
number the data does not contain (mutant 2 in `BROKEN-mutants.py`).

**The lottery read** uses the posted **floor** (an offer can land there) and the
**worst case across plausible SOCs** (the student does not choose the code):

| Read | Condition (in-force rule, posted floor) | What the student does |
|---|---|---|
| `CLEARS-LEVEL-II` | every plausible SOC: level_min ≥ 2 | apply/tailor if the scorer agrees |
| `SOC-SENSITIVE` | the code alone flips 1 entry vs 2+ (some SOC has level_min ≥ 2, another has level_max ≤ 1) | ask the recruiter which SOC code and wage level the LCA will use |
| `BRACKET-UNRESOLVED` | the floor sits in a percentile interval that straddles a cut-off | check the OFLC table for the worksite before negotiating |
| `LEVEL-I-AT-BEST` | every plausible SOC: level_max ≤ 1 | negotiate above the next published percentile, or accept single-entry odds |

A `below_level_I_possible` flag is added when any plausible SOC puts the floor
under the Level I proxy. Under the rule, such a wage can still be registered if
an acceptable alternative wage source supports it, and it is then entered once.
So it counts as 1 entry, never 0, and the report tells the student the
employer would need that survey. (v0.1.0 first mapped this case to 0 entries and
"cannot file". A read of the rule summary during verification corrected it; see
the worked run.) Reasoning for floor + worst case: the reported USCIS practice
for multiple worksites is to use the lowest applicable level (SOURCES.md). The optimistic read would mislead a student exactly when the
stakes are highest.

## Phase gates

Gates are hard stops (P4). Machine gates halt with an exit code before any file
is written. Human gates hold every affected row in `MANUAL-CHECK` until the
named file says `confirmed: true`.

| Gate | Kind | Testable handoff condition | On failure |
|---|---|---|---|
| **G0 — Timeline** | machine, over your-input | ≥ 1 registration window with `opens ≥ as_of + hiring_lag_days` **and** `opens ≤ authorized_through` (OPT end, or OPT end + STEM months). Timeline is a gate, not a vote. | exit 3, nothing written: no lottery the persona can enter means no wage to bracket |
| **G1 — Board map** | human | each board used has `confirmed: true` + `confirmed_by` in `boards.json`, and was confirmed within 30 days | that company → `MANUAL-CHECK` `board-not-confirmed` |
| **G2 — Liveness** | machine | board API returns HTTP 200 with ≥ 1 posting; the posting is present at fetch time; a replayed snapshot is 0–7 days old (local date). Liveness is a gate, not a vote; a non-live posting is never bracketed or scored. Cross-check a sample with `npm run ats:liveness`. | board → `MANUAL-CHECK` `board unresolved`; stale snapshot → exit 5 |
| **G3 — SOC map** | human | the posting's title family has `confirmed: true` and a `confirmed_by` line in `soc-map.json` | row → `MANUAL-CHECK` `soc-map-not-confirmed` (run-1 held here) |
| **G4 — Read and release** | human | a named human ticks both boxes and signs the "Human gate G4" block of `lottery-weight.md`, and that signature is logged in the run log | nothing leaves the report: the script sends no application and no message |

## Workflow

1. **G0.** Read the persona; compute `authorized_through`, every window's
   reachability, and the scorer timeline factor (the network-targets recipe's
   formula: `min(1, (opt_start + ceiling − max(as_of + lag, opt_start)) / ceiling)`).
2. **Conformance.** Parse the OEWS xlsx with the standard library. Halt (exit 4)
   if any required column is missing, the area is not `U.S.`, or the file is
   unreadable. Percentiles that are suppressed or top-coded (`*`, `#`) make that
   SOC `missing`. Non-ascending percentiles also make it `missing`, never coerced.
3. **G1/G2.** For each confirmed board: list postings, keep data-titled ones,
   fetch Greenhouse detail with pay transparency, drop contact emails/phones from
   stored text, record HTTP status and totals.
4. **Filter (audit counted).** Data-titled → drop non-US locations → drop
   senior/`II–IV`/intern/contract titles → entry-eligible US postings.
5. **Pay evidence.** Use the ATS's structured field first: Greenhouse
   `pay_input_ranges` (USD, lowest min / highest max across ranges), Lever
   `salaryRange` (`per-year-salary` only), or Ashby `Salary` component (`1 YEAR`
   only). If there is none, fall back to a **strict** text parse: exactly one
   distinct `$X – $Y` range, with an annual cue nearby and no hourly-only cue,
   quoted verbatim for G4. Anything else → `MANUAL-CHECK` with the reason.
6. **G3 + bracket.** Match the title to a family. If the family is confirmed,
   bracket the floor and ceiling under each plausible SOC, for the in-force rule
   and the DOL proposal. Then derive the lottery read.
7. **Score.** Send every entry-eligible live posting to `role-scorer.mjs`:
   sponsorship tier p (record; tier rule your-input), liveness 1.0 (record),
   timeline factor (your-input). Fit is not scored. The lottery read sits beside the
   scorer's recommendation and is never folded into it.
8. **Write** `lottery-weight.json` (agent log), `lottery-weight.md` (human
   report), `board-snapshot.json` (replayable, redacted), `roles.json`,
   `role-scores.{json,md}`.
9. **Verify.** Replay the snapshot (`--snapshot`, same `--as-of`), then run
   `verify_runs.py <live> <replay>` (decisions identical, ladder vs compact CSV,
   sponsorship vs direct CSV read, scorer arithmetic, no probability / PII keys).
10. **G4.** A human reads the report, checks every parsed-text quote against the
    posting, signs, and logs the run in `logs/runs/2026fa-AkshitVerma-AV-<n>.md`.

## What it can and cannot verify

### Can verify (record)

- That a posting was present on the company's public board at a stated UTC time,
  and what the board's own structured pay field said. Sigma's two postings have no
  structured field; their pay is a quoted sentence, labeled `parsed-text`.
- The company's 80 Days row: approvals, denials, approval rate, top sponsored titles.
- The national May 2024 OEWS P10/P25/P50/P75/P90 for each plausible SOC, and
  which published-percentile interval a given wage falls in.
- That O*NET's alternate-title sample lists a given title under a given
  occupation. "Data Analyst" appears under **7 occupations** (13-2099, 15-1243,
  15-2041, 15-2051, 15-2099, 19-3022, 19-4061).
- The existing scorer's recommendation and its per-term arithmetic.

### Cannot verify (stated in every report)

- **The worksite's real wage level.** OFLC's July 2026 – June 2027 table (built
  on May 2025 OEWS, by area) is not in the repo. The mode uses the *national*,
  one-year-older ladder. In high-cost metros (Boston, New York, San Francisco),
  local prevailing wages are expected to run above national, so the brackets
  are likely **optimistic** there. That direction is a judgment, not checked locally.
- **The SOC code that will be filed.** The employer's counsel chooses it after
  the offer. G3 lists codes a human judged plausible, and the read is
  conservative across them, but the filed code may not be on the list.
- **Odds.** Entries are not probabilities. A search on 2026-10-19 found no USCIS
  breakdown of the FY2027 registration pool by wage level, so the mode computes
  no selection rate.
- **The offer.** A posted range is a range. Klaviyo's says it spans "all our US
  locations", so the Boston floor may be higher than $112,000. The mode uses
  the published floor.
- **Title-level sponsorship.** 80 Days counts are company-wide. Klaviyo's
  `median_salary_offered` ($126,000) covers every sponsored title, mostly
  software engineering, and is never compared with a data posting.
- **Funding freshness.** Sigma's CSV row shows latest funding 2024-04-05, but
  its own posting text says it raised a Series E in May 2026. Funding is not an
  input here, and the staleness is noted, not corrected.
- **STEM OPT employer eligibility.** The three-round count assumes the employer
  uses E-Verify. The mode does not check.
- **Whether a rule changes.** The DOL proposal is shown as a scenario column,
  never as the read. If it is finalized, the in-force thresholds in `RULES`
  must change, and so must the recipe version.
- **Fit.** The scorer's fit term (weight 0.30) is not supplied, so every
  composite here is sponsorship alone. A Proven sponsor scores 0.315, just over
  the 0.30 Apply line.

## Output contract

Two artifacts, two readers (P5). Both are written into `--out-dir` on every
successful run.

### Agent log — `lottery-weight.json`

```json
{
  "recipe": "data-lottery-weight", "recipe_version": "0.1.0", "as_of": "YYYY-MM-DD",
  "run":     {"command": "...", "persona": "...", "persona_fictional": true, "boards": "...",
              "soc_map": "...", "offers": "...", "board_mode": "live|snapshot|none"},
  "sources": {"oews": "...", "sponsorship": "...", "scorer": "...", "tier_rule": {"value": {}, "source": "your-input"},
              "rules": {"current": {"thresholds": [17,34,50,67], "status": "in force"},
                        "dol-nprm-2026": {"thresholds": [34,52,70,88], "status": "PROPOSED, NOT IN FORCE"}},
              "soc_map_confirmed_by": "..."},
  "timeline": {"authorized_through": {"value": "...", "source": "your-input"}, "attempts": [
                 {"fiscal_year": 2028, "opens": {"value": "2027-03-01", "source": "your-input", "assumed": true},
                  "reachable": true, "why_not": []}],
               "attempts_reachable": 3, "scorer_factor": 1.0, "formula": "..."},
  "audit":    {"boards_fetched": 16, "boards_unresolved": 0, "postings_total": 1264, "data_title_postings": 20,
               "excluded_title_rule": 14, "excluded_non_us": 3, "entry_eligible_us": 3},
  "counts":   {"postings_assessed": 3, "by_read": {"CLEARS-LEVEL-II": 2, "BRACKET-UNRESOLVED": 1},
               "manual_check": 0, "offers": 4, "offers_assessed": 3},
  "rows": [{"kind": "posting|board", "company": "...", "title": "...", "location": {"value": "...", "source": "record"},
            "url": "...", "liveness": {"value": "live", "source": "record"}, "sponsorship": {"tier": "Proven", "p": 0.9},
            "status": "ASSESSED|MANUAL-CHECK", "reason": null,
            "pay": {"value": {"min": 0, "max": 0, "method": "structured|parsed-text", "quote": "..."}, "source": "record"},
            "soc_family": "...", "per_soc": [{"soc": "15-2051", "status": "ok|missing", "ladder": {"value": {}, "source": "record"},
            "rules": {"current": {"floor": {"pct_interval": [25, 50], "level_min": 1, "level_max": 2,
            "entries_min": 1, "entries_max": 2}, "ceiling": {}}, "dol-nprm-2026": {}}}],
            "lottery_read": {"read": "...", "worst_case_entries": 1, "best_case_entries": 2,
                             "below_level_I_possible": false, "socs_considered": [], "socs_missing": []},
            "scorer": {"recommendation": "Apply", "composite": 0.315, "arithmetic": "...", "source": "role-scores.json"},
            "next_action": "..."}],
  "offers": ["same shape as a posting row, kind = offer, location/pay source = your-input"],
  "never_computed": ["selection probability ...", "the worksite prevailing wage ...", "the SOC code the employer will file ..."]
}
```

Every value is either wrapped as `{"value", "source"}` or sits in a block
whose source is named. No key named `probability` exists, and a test enforces it.

### Human report — `lottery-weight.md`

Sections in this order. Each is checked by a test or by the attestation:

| Section | Columns / content | Reader | Decision it enables |
|---|---|---|---|
| Executive summary | plain language, no scheme names (P9) | student | whether to read further |
| Your lottery rounds (G0) | fiscal year · opens (assumed?) · reachable · why not | student | how many shots; offer-by date |
| Postings | company · posting link · location · posted base (source) · lottery read · entries at floor · scorer · next action | student | which postings deserve an application |
| Per-posting SOC table | SOC · OEWS occupation · P10–P90 · floor percentile interval · level now · entries now · level under the DOL proposal · why plausible (source) | student, recruiter conversation | what to ask about SOC/level |
| Offers and scenarios | scenario · title · worksite · base · read · entries · status · next action | student | negotiate or not |
| Needs a human look | company · item · location · pay found · reason · next action | student | the manual list |
| What this report cannot tell you | fixed list (above) | student | how much to trust the reads |
| Human gate G4 | two checkboxes, signature, date | student | release |
| Run record | recipe, inputs, audit counts, pre-scorer skip, scorer inputs, parsed-text quotes | reviewer/agent | reproduce the run |

## Stop conditions — when the mode refuses to produce a read

| Condition | Behavior | Exit / status |
|---|---|---|
| No reachable registration window (G0) | halt before writing anything | exit 3 |
| OEWS file unreadable, column missing, non-U.S. area | halt before writing anything | exit 4 |
| Snapshot older than 7 days or dated after `as_of` | halt | exit 5 |
| Scorer exits nonzero | halt; no report | exit 6 |
| `--out-dir` inside the repo but outside this contribution's namespaces | halt | exit 2 |
| No structured pay and no unique annual text range | no bracket | `MANUAL-CHECK` `no-pay-found` / `pay-ambiguous` |
| Hourly, non-USD, inverted, or out-of-bounds ($20k–$1M) pay | no bracket | `MANUAL-CHECK` with the reason |
| Title matches no SOC family, or family not confirmed | no bracket | `MANUAL-CHECK` (G3) |
| Every plausible SOC has a suppressed/top-coded/missing ladder | no read | `MANUAL-CHECK` `NO-BRACKET` |
| Asked for odds of selection | not computed, ever | listed under `never_computed` |

## Proposed additions

Each is a typed TODO. None blocks the sample path above. Each would replace an
assumption the report currently has to state as a limitation.

1. **[TODO: DATA SOURCE] OFLC prevailing-wage table, wage year 2026-07 → 2027-06**,
   from the FLAG "Wage Data Downloads" page (area × SOC × Level I–IV, built on
   May 2025 OEWS). It goes in `data/oflc/` with a provenance note. It belongs here
   because it is the only source of the real dollar cut-offs for a worksite. It
   removes both the national-proxy gap and the vintage gap, and turns
   `BRACKET-UNRESOLVED` into a single level.
2. **[TODO: DATA SOURCE] DOL OFLC LCA disclosure data (H-1B), FY2025–FY2026.**
   Employer × job title × SOC × wage level, as actually filed. It belongs here
   because it replaces the human G3 guess with what *this* employer filed for
   "Data Analyst" last year, and it gives title-level wages instead of the
   company-wide median.
3. **[TODO: DATA SOURCE] metro OEWS + BEA RPP files for `npm run bls:local-wage`**
   (`data/bls/local-wage/metro_oews.csv`, `bea_rpp.csv`, `bls_bea_msa_crosswalk.csv`,
   from PR #43; not on `main`). It belongs here as an interim metro proxy until
   item 1 lands.
4. **[TODO: DEV] Windows interpreter path in `scripts/bls/local-wage-adjustment.py`.**
   `_ensure_venv()` only looks for `.venv/bin/python`, so on Windows it exits 2
   even with a venv (`.venv/Scripts/python.exe`). Found in this run's baseline.
   A maintained file, so it is proposed here, not patched.
5. **[TODO: DEFINE] FY2028 registration window dates.** Replace the assumed
   `2027-03-01` (and later years) once USCIS announces them. Every report flags
   the assumption until then.
6. **[TODO: DATA SOURCE] E-Verify employer status** for each board company.
   STEM OPT requires an E-Verify employer; without it, the persona has 1
   reachable round, not 3 (see the no-STEM test).

## Verification checks (run before G4)

- `python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight -p "test_*.py"` → 34 tests, OK.
- `python3 …/fixtures/BROKEN-mutants.py` → 3/3 mutants killed (strict edge, interpolation, ceiling-instead-of-floor).
- `verify_runs.py <live> <replay>` → decisions identical; P50 equals the compact CSV median for every SOC; sponsorship equals a direct CSV read; composite equals hand arithmetic; no probability or PII keys.
- `npm run ats:liveness -- <posting urls> <one fabricated url>` → postings active, the fabricated one expired.
- `node scripts/conformance.mjs scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/` and `node scripts/pii-scan.mjs`.

## Run-log template (`logs/runs/2026fa-AkshitVerma-AV-<n>.md`; never edit `logs/RUN_LOG.md` directly)

```markdown
## YYYY-MM-DD — data-lottery-weight run <n>

- **Recipe:** recipes/cases/2026fa/AkshitVerma-AV-data-lottery-weight.md v<version>
- **Persona:** <path> (fictional: yes/no) · as_of: <date> · board mode: live | snapshot (<fetched_at UTC>)
- **Inputs:** 80 Days CSV; national OEWS May 2024 xlsx; soc-map.json (G3 by <name>, <date>); boards.json (<n> confirmed); offers: <path or none>
- **Command:** `<verbatim>`
- **Outputs:** <out-dir>/lottery-weight.{json,md}, board-snapshot.json, roles.json, role-scores.{json,md}
- **Result:** <data-titled> data-titled → <entry-eligible> entry-eligible US · reads: <read counts> · MANUAL-CHECK <n> · offers <n> (bracketed <n>)
- **Gates:** G0 <reachable rounds> · G1 <confirmed>/<total> · G2 live <n> / unresolved <n> · G3 <families confirmed> · G4 signed by <name>, <date> | pending
- **Verification:** replay identical yes/no · tests <n> OK · mutants <k>/<n> killed · pii-scan <result>
- **Open issues:** <list>
```

No contact details, no private application notes, no real offer amounts for a
real person in a tracked file. A real offer goes in `private/`, and so does its report.
