# CHANGE-BRIEF — Pre-OPT Data Network Targets

## Executive summary

I am designing a **network-targets** recipe for an MS Information Systems student on
F-1 who has **not started OPT yet** and is aiming at **Data Analyst / Data Engineer**
roles. It takes companies that have a DOL record of sponsoring *data* job titles,
checks whether they have a live data posting right now, and turns the ones the
scorer rejects for "no live posting" into a **network, don't apply** list. A
pre-OPT student has months before they can start work. That time is better spent
on informational interviews before a role opens than on applications to postings
that don't exist yet. This brief records my predictions *before* building. Later
revisions are appended in §7, and the original text is left as it was.

## 1. Career situation and engine layers

**Who:** International MSIS student (STEM-designated program), F-1, graduating in
a future term, OPT not yet filed or approved. Targets: Data Analyst (O*NET
15-2051.01 Business Intelligence Analysts) and Data Engineer (O*NET 15-1243.01
Data Warehousing Specialists, alt-title "Big Data Engineer"). Every employer must be
willing to sponsor H-1B later, because OPT is temporary.

**Why pre-OPT changes the problem:** the student cannot start work until the EAD
start date, so the timeline gate is about *when* a role would start, not whether
it is open today. A company with no opening today but a strong record of
sponsoring data roles is a better use of the networking hours than of the
applying hours.

**Layers used:**
- **80 Days to Stay** for sponsorship history and CSV funding fields.
- **SEC Form D samples** for funding recency where a sample joins.
- **Job-Ops** for the ATS board check (Greenhouse / Lever / Ashby public board APIs).
- **Cognitive Pivot** (BLS compact) for wage context only. It is reported outside
  the scorer, because `role_quality` weight is 0.0 (Fact 1).

The persona is fictional, with `@example.com` contact details. No real résumé or
tracker data is used.

## 2. What I reuse and what I propose

### Reused (exact paths, all exist on a fresh clone)

| Path | Use |
|---|---|
| `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | `Total Approvals`, `Total Denials`, `Approval_Rate`, `top_job_titles_sponsored`, `latest_funding_date`, `latest_funding_stage`, `website`, `state` |
| `data/sec/form-d/processed/sample/companies-sec-2025q{2,3,4}-d.sample.json`, `…2026q1-d.sample.json` | Form D `filing.date_filed`, `funding.total_amount_sold`, joined on normalized name |
| `data/bls/compact/soc_occupation_compact.csv` | `annual_median_wage` for 15-2051.01 / 15-1243.01 (context, not a vote) |
| `scripts/score/role-scorer.mjs` (`npm run score`) | the decision itself. My prototype writes a `roles.json` and calls it with `--out-dir`. I do **not** copy the scorer |
| `scripts/ats/providers/{greenhouse,lever,ashby}.mjs` | reference for the public board endpoints my board check reads |

### Measured before building (my own run on the shipped data, 2026-10-03)

- The CSV has 30,369 rows. Only **1,557** have a sponsorship record (`Total Approvals` filled).
- Of those, **121** list a data-type title (data analyst/engineer, BI, ETL,
  data warehouse, analytics engineer) in `top_job_titles_sponsored`. **13** are in MA.
- Only **3 of the 121** have a `latest_funding_date` within 24 months of today.
- The four Form D samples (50 companies each) join to only **15** CSV rows by
  normalized name. **One** of those (Databricks, 2025Q4) also has a sponsorship record.

### Proposed additions (not in the repo yet)

- **[TODO: DEV] company → ATS board map.** The CSV has `website` but no ATS
  slug, so nothing in the repo maps a company to its Greenhouse/Lever/Ashby
  board. For the prototype, the board slug is **your-input** in a small YAML or
  JSON file. Reason it belongs: without it, "no live posting" can't be
  checked at company level, only per URL (`ats:liveness`).
- **[TODO: DEV] a "network, don't apply" bucket.** The scorer only knows
  Apply / Consider / Skip. My recipe post-processes the scorer's own
  `role-scores.json`. A Skip gated **only** by liveness, with a strong
  sponsorship vote, becomes a network target. This changes no scorer rule.
- **[TODO: DATA SOURCE] full Form D quarters.** Recent funding mostly can't be
  checked on a fresh clone (Fact 3). The recipe says so and does not treat
  missing Form D as "not funded."

## 3. Gates and what a human needs to see

| Gate | Testable condition (paths that exist) | Human must see |
|---|---|---|
| **G0 Timeline** | persona OPT start/end dates parse; OPT end is after the run date; start ≤ end | the dates (your-input) and the hiring-lag assumption, which is labeled your-input and not a record |
| **G1 Entity match** | `candidates.json` in my output folder; every row has `match_method` and the CSV row it came from | name collisions (e.g. a generic name like "HUMAN INC" could be a different firm than its `website`). The human confirms or strikes each company before any network call |
| **G2 Liveness (board check)** | `board-snapshot.json` exists, `fetched_at` < 7 days old, every company is `live` / `none` / `unresolved` | that `unresolved` (404, wrong slug, unknown ATS) is **not** the same as `none`. Only `none` can become a network target |
| **G3 Outreach sign-off** | `network-targets.md` written; nothing is sent anywhere | the human picks who to contact. The recipe never drafts messages to real named people |

## 4. Predicted failure cases and how I'll check each

1. **Company missing from the CSV, or present with no sponsorship record.**
   Absence in DOL data can mean a name-match miss, not "never sponsored." Check:
   a fixture company that isn't in the CSV must come out `sponsorship: unknown`.
   It must not get `p = 0` and must never land on the network list.
2. **ATS board 404s or the slug is wrong.** Check: a fixture board response with
   HTTP 404 must produce `unresolved` and stop that company at G2. It must not
   turn into `liveness = 0` and then a network target.
3. **SOC code with no row in the BLS compact file** (e.g. a legacy code like
   15-1199). Check: the wage-context field reads `missing` and the run continues
   without inventing a wage.
4. **OPT date already past, or start after end.** Check: a persona fixture with
   `opt_end_date` in the past must exit non-zero at G0 with no outputs written.
5. **Title regex errors.** False positives ("Data Admin", "Data Integrity
   Specialist") and false negatives ("Consultant – Analytics"). Check: a
   hand-labeled list of real `top_job_titles_sponsored` strings in a fixture.

## 5. What I predict the prototype will get wrong on the first pass

- **The funding vote will be nearly empty.** With 3 of 121 candidates funded in the
  last 24 months and one Form D join, the list will be ranked almost entirely
  on sponsorship volume. So it will skew toward **large employers** (Amgen,
  Pinterest, DocuSign), not the funded startups the network-targets idea
  imagines.
- **`top_job_titles_sponsored` is a short top-N list**, so a company that sponsored
  data engineers outside its top titles will be missed. These false negatives will
  hit big SWE-heavy employers hardest.
- I expect the board check to be `unresolved` for most companies on the first
  pass, because slugs are hand-supplied.

## 6. Out of scope

Live scraping of non-public ATS pages; Workday boards; any outreach automation;
any change to `role-scorer.mjs` weights.

## 7. Revisions

*(append-only, dated, below this line)*

### 2026-10-03 — Recipe review (human decision)

- **Accepted:** the sponsorship tier rule (Proven ≥50 approvals and ≥90% rate;
  Likely ≥10; Possible 1–9), leaving fit out of the scorer input, and treating a
  board with zero postings total as `unresolved`.
- **Changed:** funding is no longer a ranking aid. It is now a **requirement**
  for the NETWORK bucket (a funding record within 24 months).
- **Consequence, measured right after the decision:** of 121 candidates, 91 are
  Proven/Likely. Only **2** of those have recent funding evidence (Outset Medical,
  Centific Global Solutions, both Likely), so NETWORK holds at most 2 companies on
  a fresh clone. Strong sponsors blocked only by funding are reported as
  `network-blocked`, not hidden.
- **Prediction §5 partly wrong already:** I predicted the list would skew toward
  large employers ranked on sponsorship. Under the new rule, large employers
  can't reach NETWORK at all, because their CSV funding dates are old.
- **New blind-spot example:** Databricks is the only Form D sample match with
  sponsorship history, but none of its top sponsored titles is a data title,
  so it never becomes a candidate (§4 case 5 / top-N blind spot).

### 2026-10-03 — Prototype build: corrected counts and new findings

- **Correction:** the prototype's final title patterns (added `BI Engineer` and
  `data warehous*`) find **123** candidates, not 121. The two added are 23andMe
  ("Lead BI Engineer") and WW International ("Director Data Warehousing"). Both
  qualify only through *senior* titles. Proven/Likely is now **93** (49 + 44).
  Recent funding is unchanged: 3 of 123 overall, and 2 of the Proven/Likely, so
  NETWORK still holds at most 2. The §2 and earlier §7 figures are left as written.
- **§4 case 5 confirmed in the first test run:** I hand-labeled "Senior AV Safety
  Data and Analytics Engineer" (a real Zoox title) as a non-data title. It
  contains "Analytics Engineer" and matches. The label was wrong, not the regex.
  "Consultant – Analytics" is still missed, and that is pinned in a test as a
  known gap.
- **New from building:** Ashby's API returns 403 without a `User-Agent` header.
  Some CSV `website` values look generated from the name (`social-finance.com`
  for SoFi). The Windows console can't print `✓` (cp1252).
- **§5 third prediction so far:** of the board names probed, 16 of 24 resolved on
  Greenhouse, Lever or Ashby, so "most `unresolved`" was too pessimistic *for the
  probed set*. The other 99 candidates have no board in the map at all.

### 2026-10-03 — After the live run (run-1) and the v0.1.1 fix (run-2)

- **run-1 (live, v0.1.0):** APPLY-TAILOR 3 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 12.
- **What run-1 got wrong:** Zoox reached APPLY-TAILOR only on "Contract Student
  Worker – Data Analyst (Part-time)" postings. I hadn't predicted this failure
  case in §4: a posting that matches the title pattern but is the wrong *kind*
  of job (contract, part-time, student) for a sponsored full-time hire.
- **Human decision:** exclude contract / student worker / part-time / co-op /
  temporary titles (persona, your-input), and flag senior-only sponsorship
  evidence without changing any bucket.
- **run-2 (replay of run-1's snapshot, v0.1.1):** only Zoox changed
  (APPLY-TAILOR → SKIP, `network-blocked: funding stale`). APPLY-TAILOR 2 ·
  NETWORK 1 · MANUAL-CHECK 107 · SKIP 13.
- **§5 scorecard:** "funding vote nearly empty" → correct (2 of 93 Proven/Likely).
  "Skews to large employers" → wrong under the funding rule (large employers can't
  reach NETWORK). "Board check mostly unresolved" → wrong for the 16 probed
  boards (all fetched); right for the other 107 candidates, which have no board
  in the map. Not predicted: 53 of 123 candidates (43%) have senior-only
  data-title evidence.
