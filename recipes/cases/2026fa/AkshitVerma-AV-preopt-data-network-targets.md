---
status: RUNNABLE-SAMPLE   # DRAFT | SPECIFIED | RUNNABLE-SAMPLE | RUNNABLE-LIVE
todos_open: 6
last_gate: "G3 signed by Akshit Verma, 2026-10-03, on course/2026fa/submissions/AkshitVerma-AV/runs/run-2/network-targets.md (G1 board map also confirmed by Akshit Verma, 2026-10-03); run log logs/runs/2026fa-AkshitVerma-AV-1.md"
attestation: null  # set only at VERIFIED. This is a sample run: shipped CSV + Form D samples + one live board fetch of 16 hand-confirmed boards.
recipe_version: 0.1.1
---

# preopt-data-network-targets — Network, Don't Apply (pre-OPT Data Analyst / Data Engineer)

## Executive summary

**What it does.** Starts from companies with a DOL record of sponsoring H-1B
workers *and* a data title (Data Analyst, Data Engineer, BI, ETL, data warehouse,
analytics engineer) among their top sponsored titles. It checks each company's
public ATS board for an open data posting today, then sends the evidence through
the existing role scorer (`scripts/score/role-scorer.mjs`). Companies the scorer
skips **only** because there is no live posting become a **network, don't
apply** list, but only if they also have a strong sponsorship record **and**
evidence of funding within the last 24 months.

**Who it is for.** An international MS Information Systems student on F-1 who
has **not started OPT yet**: graduating in December, EAD start in late January,
targeting Data Analyst (O*NET 15-2051.01) and Data Engineer (O*NET 15-1243.01)
roles. The persona in this recipe is fictional: Jack Spencer, Chicago,
`jack.spencer@example.com`.

**What it decides.** Each candidate company is put in exactly one bucket:
`APPLY-TAILOR`, `NETWORK`, `MANUAL-CHECK` or `SKIP`. The machine decides the
bucket. A human decides whether to act on it (gate G3).

**Why pre-OPT matters.** A student who can't start work for months gets little
from the application hours on postings that will be filled before the EAD
arrives. Those months are better spent in the **networking** hours of the 3-3-2
day, building relationships at sponsors of data roles that have no opening yet.

Two readers: this file is for the agent. The card
`recipes/cases/2026fa/AkshitVerma-AV-preopt-data-network-targets.card.md` is for
the person.

**Done when:** one run writes `network-targets.json` and `network-targets.md`
into the chosen `--out-dir`, and every company that entered at G1 appears in
exactly one bucket. Every value carries a `record` / `model-judgment` /
`your-input` label, and the scorer's own `role-scores.json` sits next to them.

## Required reads

1. `SNICKERDOODLE.md` (prime directive, gates), `DOMAIN.md` → Known gaps.
2. `DATA_CONTRACT.md` §Zero-Conditions. The 80 Days CSV holds company phone
   numbers and executive names. They are never copied into outputs.
3. `book/chapters/07-who-sponsors-the-80-days-sponsorship-scorer.md` (tiers are
   not pinned by the repo; this recipe states its own rule, below).
4. `scripts/score/role-scorer.mjs` (the decision core this recipe calls, not copies).
5. `data/80-days-to-stay/data/SEC_DOL_H1b_data_mapped-audit.md` (coverage: 5.1%
   of rows carry H-1B fields; no SOC codes).

## Source inventory

| Source | Path / command | Exists on fresh clone? | Label of values it yields |
|---|---|---|---|
| 80 Days CSV | `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | yes (30,369 rows) | `record` |
| Form D samples | `data/sec/form-d/processed/sample/companies-sec-{2025q2,2025q3,2025q4,2026q1}-d.sample.json` | yes (50 companies each, samples only) | `record` |
| BLS / O*NET compact | `data/bls/compact/soc_occupation_compact.csv` | yes | `record` |
| Role scorer | `npm run score -- <roles.json> --out-dir <dir>` | yes | the scorer's labels pass through |
| ATS public board APIs | `boards-api.greenhouse.io`, `api.lever.co`, `api.ashbyhq.com` (the same endpoints as `scripts/ats/providers/*.mjs`) | network | `record` (as of `fetched_at`) |
| Persona | `scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json` | added by this recipe | `your-input` |
| Board map | `scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json` | added by this recipe | `your-input` |
| Prototype | `python3 scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py` | added by this recipe | — |

**Network hosts this recipe may call:** only the three ATS API hosts above, and
only with `--live`. Without `--live`, the prototype reads a saved board snapshot
(`--snapshot <file>`) and makes no network calls.

### Run command (from repo root)

```bash
python3 scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py \
  --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json \
  --boards  scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json \
  --live \
  --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/run-1
```

Offline test: `python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets -p "test_*.py" -v`

## Inputs

| Input | Example (fictional) | Label |
|---|---|---|
| `graduation` | 2026-12 | your-input |
| `opt_start_date` (requested EAD start) | 2027-01-23 | your-input |
| `opt_end_date` | 2028-01-22 (12 months; a STEM extension is a later, separate filing) | your-input |
| `unemployment_ceiling_days` | 90 | your-input (post-completion OPT rule) |
| `hiring_lag_days` (application → offer) | 60 | your-input. An **assumption**, not a record |
| `target_title_patterns` | data analyst, data engineer, analytics engineer, business intelligence, BI analyst/developer, ETL, data warehouse | your-input |
| `target_soc` | 15-2051.01, 15-1243.01 | your-input |
| `exclude_posting_title_patterns` | senior, sr, staff, principal, lead, manager, director, head, VP; intern/internship; contract, student worker, part-time, co-op, temporary (added v0.1.1 after run-1) | your-input. A new grad can't realistically fill these, so they don't make a board `live`. They are counted as `excluded_by_title_rule` |
| `exclude_posting_location_patterns` | India, Mexico, Canada, UK, Ireland, Poland, Germany, Singapore, … | your-input. OPT employment must be in the US. The list is **incomplete** by nature |
| `preferred_locations` | Chicago, Remote | your-input. Flags live postings only, never filters companies |
| `funding_window_months` | 24 | your-input. A NETWORK target needs a funding record inside this window |
| `as_of` | run date (overridable with `--as-of` for reproducibility) | your-input |

## Evidence → scorer mapping

The prototype writes `roles.json` shaped like `data/examples/ch11-roles.json`, with
**one entry per company** (not per posting). Every term carries `source`.

| Scorer term | How it is filled | `source` |
|---|---|---|
| `sponsorship.p` / `tier` | Tier rule below, applied to the CSV's `Total Approvals` and `Approval_Rate` | `record` (the counts). The thresholds are `your-input`, recorded in `basis` |
| `liveness.factor` | `1.0` if the board returned ≥1 posting matching a target title; `0.0` if the board returned postings but none match | `record` |
| `timeline.factor` | Formula below, from persona dates | `your-input` |
| `fit` | **Omitted.** Fit can't be judged at company level without reading a posting. The human judges fit on the posting in the APPLY-TAILOR bucket | — |
| `role_quality` | **Omitted.** Its weight is `0.0` in the scorer (Fact 1). The BLS wage is reported as context in the Markdown report only | — |

**Sponsorship tier rule** (`your-input`, [VERIFY]; Ch.7 says the repo's own
thresholds are unreconciled):

| Tier | Condition on CSV record | p |
|---|---|---|
| Proven | `Total Approvals ≥ 50` and `Approval_Rate ≥ 90` | 0.90 |
| Likely | `Total Approvals ≥ 10` (and not Proven) | 0.60 |
| Possible | `Total Approvals` 1–9 | 0.40 |
| None | `Total Approvals` = 0 | 0.00 |
| unknown | field empty or company absent | **not scored**. Never `p = 0` |

**Timeline formula** (`your-input`):
`deadline = opt_start + unemployment_ceiling`,
`earliest_start = max(as_of + hiring_lag, opt_start)`,
`slack = deadline − earliest_start` (days),
`factor = 0 if slack ≤ 0 else min(1, slack / unemployment_ceiling)`.
For Jack on 2026-10-03, `earliest_start = 2027-01-23` and `slack = 90`, so the factor is
1.0. The factor drops as the unemployment clock runs, and the gate closes at 0.

**What this mapping means for the scorer's arithmetic** (weights from
`role-scorer.mjs`): with `fit` omitted, the composite is `0.35 · p · liveness · timeline`.
- Live Proven → 0.315 → Apply. This is just above the 0.30 threshold, so a Proven
  Apply comes from **sponsorship alone** and needs a human fit check.
- Live Likely → 0.21 → Consider.
- Live Possible → 0.14 → Skip.
- Any board with no data posting → gated Skip.

## Proposed additions

1. **[TODO: DEV] company → ATS board resolver.** The CSV has `website` but no
   ATS slug. `boards.json` is hand-filled (`your-input`) and each entry must carry
   `"confirmed": true` before it is used. Belongs in `scripts/ats/` because
   company-level liveness ("is anything open here?") is a different question
   from `ats:liveness` ("is this URL open?").
2. **[TODO: DEV] `NETWORK` bucket in the engine.** It is implemented here as a
   post-processor over the scorer's own `role-scores.json`, with no scorer
   change. A maintainer could adopt it as a fourth recommendation.
3. **[TODO: DATA SOURCE] title-level H-1B counts.** `Total Approvals` is
   company-wide, and `top_job_titles_sponsored` is a short top-N list with no SOC
   code. Raw DOL LCA disclosure files (with `SOC_CODE` and `JOB_TITLE`) would let
   the sponsorship vote be data-role-specific.
4. **[TODO: DATA SOURCE] full Form D quarters** (Fact 3). Only the four
   50-company samples ship. Missing Form D is reported as `not-in-sample`,
   never as "not funded."
5. **[TODO: DEV] Chicago metro wage.** `npm run bls:local-wage` fails on a fresh
   clone (Facts 2 and 7), so the report shows the **national** median only and
   says so.
6. **[TODO: DEV] Workday / iCIMS boards.** Many large sponsors (e.g. Amgen) post on
   ATSs this recipe can't read. They land in `MANUAL-CHECK`.

## Phase gates

Hard stops. Each condition is testable against paths that exist.

| Gate | Testable condition | Pass → | Fail → |
|---|---|---|---|
| **G0 Timeline** | persona dates parse; `opt_end_date > as_of`; `opt_start_date ≤ opt_end_date`; timeline factor > 0.05 | build candidates | exit code 3, message names the failed date, **no outputs written** |
| **G1 Entity match + board map** | `<out>/candidates.json` written. A company is checked only if `boards.json` has an entry for its exact CSV `company_name` with `"confirmed": true` | board check for confirmed entries | unconfirmed or unmapped → `MANUAL-CHECK` (reason `no-confirmed-board`), **no network call** |
| **G2 Liveness** | `<out>/board-snapshot.json` has `fetched_at` ≤ 7 days before `as_of`. Each company is `live` / `none` / `unresolved` | `live` and `none` go to the scorer | `unresolved` (HTTP ≠ 200, network error, or a board returning **zero postings total**) → `MANUAL-CHECK`. Never sent to the scorer, because a missing `liveness` defaults to 1.0 in `role-scorer.mjs` |
| **G3 Outreach sign-off** | `<out>/network-targets.md` exists | the human chooses whom to contact and records it in the run log | — (the recipe sends nothing and drafts no messages to real people) |

A board that returns zero postings total counts as `unresolved`, not `none`. The
usual cause is a company that moved to another ATS, and treating it as "no
openings" would invent a network target.

## Workflow

1. **G0.** Load the persona and compute the timeline factor. Stop on failure.
2. **Candidates.** Read the CSV. Keep rows with a non-empty `Total Approvals`
   where at least one entry of `top_job_titles_sponsored` (parsed as a list)
   matches a target title pattern. Keep only these columns: `company_name`,
   `state`, `website`, `Total Approvals`, `Total Denials`, `Approval_Rate`,
   `median_salary_offered`, `latest_funding_date`, `latest_funding_stage`, plus
   the matched titles. **Drop** `phone`, `executive_officers` and `board_directors`.
3. **Funding evidence (a NETWORK requirement).** Join each candidate to the Form D
   samples on lowercase-alphanumeric normalized name. Record `form_d: {quarter,
   date_filed, total_amount_sold}` or `not-in-sample`. Set `funding_evidence`:
   - `recent`: the CSV `latest_funding_date` **or** a Form D sample `date_filed`
     falls within `funding_window_months` before `as_of` (`record`; the window is
     `your-input`).
   - `stale`: a dated record exists, but every date is older than the window.
   - `none-in-shipped-data`: no funding date and no Form D sample hit. This means
     the shipped data is silent, **not** that the company is unfunded (Fact 3).

   Funding is applied **after** the scorer, as a condition on the NETWORK bucket.
   The scorer has no funding term, and adding one would mean changing it.

   **Why funding is a requirement** (your-input, Akshit Verma's decision,
   2026-10-03): networking takes weeks to pay off, so the hours should go to
   companies likely to be *adding* data headcount before the OPT start. A recent
   raise is the only forward-looking signal in the engine; sponsorship history
   only looks back. A sponsor with no recent funding and no open data role may
   simply not be hiring. "Recent funding → hiring" is a **hypothesis, not a
   record**. The cost is accepted knowingly and reported: on the shipped samples
   the rule leaves 1 NETWORK target and blocks 13 strong sponsors, all listed as
   `network-blocked`. The preferred fix is better data (full Form D quarters), not
   a wider window, because a wider window weakens the forward-looking signal.
4. **G1.** Write `candidates.json`. Look each company up in `boards.json`.
5. **G2.** For confirmed boards: with `--live`, GET the ATS API (timeout 15 s, no
   retries, one request per company, with a `User-Agent` header, because Ashby
   returns 403 without one). Without `--live`, read `--snapshot`; a snapshot more
   than 7 days older than `as_of` stops the run with exit 5. Classify each company:
   - `live`: at least one posting matches a target title **and** is not excluded
     by seniority/intern or by non-US location.
   - `none`: the board returned postings, but none qualify.
   - `unresolved`: HTTP ≠ 200, network error, or zero postings total.

   Write `board-snapshot.json` with every posting's title, location and URL, so
   a later replay with different patterns needs no network.
6. **Score.** Write `roles.json` for `live` and `none` companies only. Run
   `node scripts/score/role-scorer.mjs <out>/roles.json --out-dir <out>`. The
   scorer writes `role-scores.json` and `role-scores.md`.
7. **Bucket.** Read the scorer's `role-scores.json`:
   - `APPLY-TAILOR` — `recommendation` is Apply or Consider.
   - `NETWORK` — `machine_recommendation` is Skip, `reason` starts with
     `gated: liveness`, the tier is Proven or Likely, **and**
     `funding_evidence` is `recent`.
   - `SKIP` — every other scored company. A company that meets every NETWORK
     condition **except** funding gets the skip reason `network-blocked: funding
     stale` or `network-blocked: no funding evidence in shipped data`. The report
     counts these separately, so the human can see what the funding rule cost.
   - `MANUAL-CHECK` — every G1/G2 failure, with its reason.
8. **Report.** Write `network-targets.json` (agent) and `network-targets.md` (person).
9. **G3.** Stop. The human reads the report.

## What it can and can't verify

### Can verify (record)

- That the CSV row exists and holds these approval and denial counts, this
  approval rate, and these title strings. A grader can check each by hand with
  `grep`.
- That a target title pattern matches one of those title strings (deterministic regex).
- That the ATS API returned HTTP status X and N postings, M of which matched a
  target title, at `fetched_at`.
- Whether a Form D sample entry with the same normalized name exists.
- The national OEWS median for BLS 15-2051 and 15-1243 from the compact file.
- What the existing scorer did with the evidence, via its own trace.

### Can't verify

- **That the company sponsors data roles specifically.** Approvals are
  company-wide. The data-title match only shows that a data title was among the
  *top* sponsored titles. The DOL fiscal-year window behind the counts isn't
  documented in the repo.
- **That the sponsorship evidence is entry-level.** v0.1.1 flags
  `senior_only_evidence` when every matched sponsored data title hits the
  excluded-title patterns (e.g. Outset Medical: only "Staff Data Engineer").
  On 2026-10-03 that was 53 of 123 candidates. The flag changes no bucket; the
  human weighs it.
- **That the company sponsors new grads, or sponsors today.** The record looks
  backward; sponsorship may have frozen since (Ch.7).
- **That the CSV row and the ATS board are the same company.** Generic names
  (e.g. `HUMAN INC`) can collide. The human confirms each mapping at G1.
- **That the company's website identifies it.** Some `website` values look
  generated from the name (e.g. `SOCIAL FINANCE INC → social-finance.com`, while
  SoFi uses sofi.com), so the website isn't treated as identity evidence.
- **That a posting is in the US.** The excluded-location list is a your-input
  heuristic. A non-US posting with an unlisted location still counts as `live`.
- **That `none` means "not hiring."** A role may be posted on another ATS, posted
  only through recruiters, or opened next week.
- **That a `live` posting is not a ghost posting.** The API listing a job proves it
  is listed, not that the company is hiring for it.
- **That a company without funding evidence is unfunded.** 3 of 123 candidates
  have a CSV funding date within 24 months of 2026-10-03, and none of the 123 joins
  to a Form D sample. Databricks joins to a sample and has sponsorship history,
  but its top sponsored titles have no data title, so it is never a candidate.
  Because funding is a NETWORK requirement, **at most 2 companies** (both Likely
  tier) can reach NETWORK with the shipped data. The other 91 Proven/Likely
  sponsors are blocked by missing data, not by evidence against them. The
  report counts them.
- **Chicago pay.** The wage shown is national. For 15-2051.01 and 15-1243.01 it is
  the *parent BLS code's* wage (Data Scientists, Database Architects), not the
  detailed O*NET occupation's.
- **Fit.** It is not scored. The human judges fit.

## Output contract

All files are written into `--out-dir`, never over a tracked repo file.

**Agent (JSON)** — `network-targets.json`:

```json
{
  "recipe": "preopt-data-network-targets", "recipe_version": "0.1.1",
  "as_of": "2026-10-03", "persona": "fixtures/persona-jack-spencer.json",
  "data_used": {"csv": "...v3.csv", "form_d": ["...sample.json"], "bls": "...compact.csv", "board_mode": "live|snapshot"},
  "timeline": {"factor": 1.0, "slack_days": 90, "source": "your-input", "assumptions": {"hiring_lag_days": 60}},
  "counts": {"candidates": 0, "APPLY-TAILOR": 0, "NETWORK": 0, "MANUAL-CHECK": 0, "SKIP": 0},
  "companies": [{
    "company": {"value": "...", "source": "record"},
    "bucket": "NETWORK",
    "sponsorship": {"approvals": {"value": 0, "source": "record"}, "approval_rate": {"value": 0, "source": "record"},
                    "tier": {"value": "Proven", "source": "your-input", "basis": "tier rule v0.1.0"},
                    "matched_titles": {"value": ["..."], "source": "record"},
                   "senior_only_evidence": {"value": false, "source": "record"}},
    "board": {"status": "none", "ats": {"value": "greenhouse", "source": "your-input"}, "http_status": 200,
              "postings_total": 0, "postings_matched": [], "fetched_at": "...", "source": "record"},
    "funding": {"latest_funding_date": {"value": "...", "source": "record"}, "form_d": "not-in-sample",
                "funding_evidence": {"value": "recent|stale|none-in-shipped-data", "source": "record", "window_months": {"value": 24, "source": "your-input"}}},
    "scorer": {"recommendation": "Skip", "reason": "...", "composite": 0, "source": "role-scores.json"},
    "next_action": "..."
  }]
}
```

**Person (Markdown)** — `network-targets.md`: an executive summary (counts per
bucket, the skip rate, data used), then one table per bucket. Every cell carries
its label in brackets. After the tables: the "can't verify" list, repeated, and
the G3 sign-off line.

Intermediate files (also in `--out-dir`): `candidates.json`,
`board-snapshot.json`, `roles.json`, `role-scores.json`, `role-scores.md`.

## Stop conditions

- Exit codes: `0` ok · `2` usage/input error or an `--out-dir` inside the repo
  but outside this contribution's namespaces · `3` G0 · `4` zero candidates ·
  `5` stale snapshot · `6` scorer failed.
- G0 fails → stop, no outputs written.
- Zero candidates after the title filter → stop with exit 4 (the title patterns or CSV changed).
- Zero confirmed boards → write outputs with everything in `MANUAL-CHECK`; exit 0 with a warning.
- The scorer exits non-zero → stop and surface its stderr. Do not bucket without the scorer.
- Never: guess an ATS slug, retry a failed board in a loop, call any host not listed above, or read `private/` / `search/resume.json`.

## Next action per bucket (the 3-3-2 day)

| Bucket | Next action | 3-3-2 block |
|---|---|---|
| `APPLY-TAILOR` | Open the matched posting URL(s), judge fit by hand, tailor one application | the **2** (apply) |
| `NETWORK` | Find one data-team employee or alum for a 20-minute informational interview; re-run the board check in 14 days | the **3** (networking) |
| `MANUAL-CHECK` | 10 minutes on the careers page: find the real ATS, fix `boards.json`, or strike the company | the **2** (research) |
| `SKIP` | Nothing. This time goes back to the day | — |

## Verification checks

- Pick one `NETWORK` row and `grep` its `company_name` in the CSV. The approvals,
  rate and titles must match the report.
- Confirm every company in `candidates.json` appears in exactly one bucket.
- Confirm `roles.json` contains no `unresolved` company.
- Confirm no output contains a phone pattern: `node scripts/pii-scan.mjs`.
- Run the offline test.

## Run-log template (`logs/runs/2026fa-AkshitVerma-AV-<n>.md`)

```markdown
## YYYY-MM-DD — preopt-data-network-targets run <n>

- **Recipe:** recipes/cases/2026fa/AkshitVerma-AV-preopt-data-network-targets.md v0.1.1
- **Persona:** fictional (path) · as_of: YYYY-MM-DD
- **Inputs:** CSV v3; Form D samples (list); boards.json (N confirmed entries); board mode: live|snapshot
- **Command:** <exact command>
- **Outputs:** <out-dir>/network-targets.{json,md}, role-scores.{json,md}
- **Result:** candidates N → APPLY-TAILOR a · NETWORK b · MANUAL-CHECK c · SKIP d
- **Gates:** G0 pass/fail · G1 confirmed N/M · G2 live x / none y / unresolved z · G3 signed by <name> / not signed
- **Human decision at G3:** <which NETWORK companies chosen for outreach, and why>
- **Open issues:** <what did not work or is still missing>
```

Never edit `logs/RUN_LOG.md`.

## Facts that bite: how this recipe handles them

| Fact | Handling |
|---|---|
| 1 role_quality weight 0.0 | Not sent to the scorer. The national wage is reported as context only. No weight proposed |
| 2 / 7 `bls:local-wage` | Not used. The Chicago wage is proposed addition #5 |
| 3 SEC samples only | The four sample files are named in `data_used`. Missing means `not-in-sample`. Because funding gates NETWORK, this fact shrinks the list to at most 2 companies on a fresh clone. The cost is reported, not hidden |
| 4 planned dirs | Every output path is under `--out-dir`. No `data/verified/` or `logs/gate-decisions/` |
| 5 `snickerdoodle` CLI | Not used. Commands are `python3` and `node` only |
| 8 `validate-h1b-join-sample.py` | Not used. The join is name-normalized and reported as such |
| Found while building: scorer defaults a missing gate to 1.0 | `unresolved` companies are never sent to the scorer |
| Found while building: `ats:scan` needs `data/ats/portals.yml` | Not used. The prototype calls the board APIs directly from `boards.json` |
