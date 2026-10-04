# FRICTIONAL — honest work log

## Executive summary

A running log of what was tried, what happened, what was checked and changed, and
who did it: me (Akshit) or the AI agent (Claude Code, Opus 5.5). Entries are
appended in order and never rewritten. Lines marked **[ME]** are my own
decisions or words. Lines marked **[AI]** are work the agent did that I reviewed.

## 2026-10-03 — Setup and toolchain baseline

- **Tried [AI]:** `npm install`, `npm run doctor`, `npm run verify` on a fresh clone of my fork (Windows 11, Node 24.19, Python 3.12).
- **Expected:** verify passes on an untouched clone.
- **Happened:** `npm run verify` **failed** with 6× `E3 … is out of sync with instructions/` (AGENTS.md, CLAUDE.md, and four other adapter files).
- **Checked [AI]:** `git config core.autocrlf` → `true`. `file CLAUDE.md` → CRLF line endings. `build-instructions.mjs` emits LF, so every generated file looked hand-edited.
- **Changed [AI]:** `git config core.autocrlf false`, `git config core.eol lf`, then re-checked out the tree (it was clean, so nothing was lost). verify then passed with 3 warnings.
- **Checked [AI]:** the W2 warnings ("private/ and data/ats/ not gitignored") are false positives. `git check-ignore -v` shows `/private/*`, `/data/ats/*` and `resume.json` are ignored. The manifest check looks for the literal string `private/`.
- **Also found [AI]:** `npm run ats:scan -- --dry-run` fails on a fresh clone: `portals.yml not found` (`data/ats/` is gitignored and only `portals.example.yml` ships). `gh` CLI is not installed. `node scripts/pii-scan.mjs` (tree mode) reports one finding already on `main`: an npm author email in `package-lock.json`. `--diff origin/main` is clean.
- **Learned (Akshit Verma):** a fresh clone is not a trusted baseline on Windows. Line endings alone broke `verify` (and, found later, `doctor`'s recipe count). Check the toolchain before trusting a failure as real. *[AI-drafted at Akshit's request, accepted by Akshit]*

## 2026-10-03 — Choosing the domain

- **[ME]** Chose the target situation the recipe is built for: an MSIS student targeting Data Analyst / Data Engineer, F-1, pre-OPT. Angle: network-targets. Working mode: step-by-step, reviewing each piece before the next.
- **[ME]** Persona details: Jack Spencer (fictional), graduating Dec 2026, OPT start 2027-01-23, Chicago. Board check: live fetch for the worked run, saved snapshot for the test.
- **[AI]** Defaults it chose and labeled your-input: OPT end 2028-01-22 (12 months), hiring lag 60 days.

## 2026-10-03 — Measuring the data before predicting (CHANGE-BRIEF)

- **Tried [AI]:** counted what the shipped data supports for data roles.
- **Found:** 30,369 CSV rows; 1,557 with H-1B fields; 121 list a data title in `top_job_titles_sponsored`; 13 in MA; 5 in IL (4 with no website). The CSV has no SOC codes, and the DOL year window isn't documented. The four Form D samples (200 companies) join to 15 CSV rows; only Databricks also has sponsorship history.
- **[AI]** drafted `CHANGE-BRIEF.md`. **[ME]** accepted it without edits. **What I'd now predict differently (Akshit Verma):** that postings can match the title but be the wrong *kind* of job (contract or student-worker), and that much of the sponsorship evidence is senior-only. Neither was in my §4/§5 predictions (see CHANGE-BRIEF §7). *[AI-drafted at Akshit's request, accepted by Akshit]*

## 2026-10-03 — Recipe and card review

- **[AI]** drafted the recipe and card. While reading `role-scorer.mjs`, it found that a missing `liveness` or `timeline` value defaults to 1.0 (an open gate), so the design keeps `unresolved` companies out of the scorer.
- **[ME] accepted:** the tier rule, omitting fit, zero-postings board = `unresolved`.
- **[ME] rejected / changed:** funding as a ranking aid only. I made recent funding (≤24 months) a **requirement** for NETWORK.
- **Checked right after my change [AI]:** only 2 of 91 Proven/Likely candidates have recent funding evidence, so NETWORK holds at most 2 companies on a fresh clone. Databricks never becomes a candidate (no data title in its top titles). Recipe, card and CHANGE-BRIEF §7 updated. Blocked sponsors are reported as `network-blocked`.
- **Why I made funding a requirement (Akshit Verma):** networking takes weeks
  to pay off, so I want the hours to go to companies likely to be *adding* data
  headcount between now and the persona's OPT start. A recent raise is the only signal in
  the engine that points forward; sponsorship history only looks back. A sponsor
  with no recent funding and no open data role may simply not be hiring, and an
  informational interview there is less likely to become an opening. I accepted
  the cost knowingly: on the shipped samples the rule leaves 1 target and blocks
  13 strong sponsors, and the report lists them rather than hiding them. "Recent
  funding → hiring" is my hypothesis (your-input), not a record. *[AI-drafted at Akshit's request, accepted by Akshit]*
- **Unresolved question:** is "at most 2 targets" a useful list, or should the window or the data source change? **Still open after run-2 (Akshit Verma):** it left 1 target. I'd rather fix the data (full Form D quarters, [TODO: DATA SOURCE]) than loosen the window, because a wider window weakens the forward-looking signal the rule exists for. *[AI-drafted at Akshit's request, accepted by Akshit]*

## 2026-10-03 — Prototype build (step 3)

- **[AI]** probed 24 candidate companies' name-derived board names on Greenhouse,
  Lever and Ashby (the three hosts the recipe names). 16 resolved. Not found
  anywhere: Centific, ByHeart, Tempus (the only Chicago Proven sponsor), Vertex
  Analytics, Amgen, Dataminr, Hinge Health, Quantiphi. Klaviyo has an Ashby board
  with **0** postings and a Greenhouse board with 133: a live example of the
  "moved ATS" case.
- **Broke:** a second probe to Ashby returned **403**. Cause: no `User-Agent`
  header (the first probe had one). **Fixed [AI]:** the prototype always sends one.
- **Broke:** the first smoke run crashed with `UnicodeEncodeError` printing `✓` on
  the Windows console (cp1252). **Fixed [AI]:** `main()` reconfigures
  stdout/stderr to UTF-8.
- **Broke:** 1 of 22 tests failed. The AI-written test hand-labeled "Senior AV Safety Data and
  Analytics Engineer" as a non-data title, but it matches `analytics engineer`.
  **Fixed [AI]:** moved it to a "borderline: matches" test. The regex was not
  weakened to make the test pass. 23/23 pass now.
- **Found:** the final regex gives 123 candidates, not 121 (23andMe, WW
  International added, both via senior titles). Recipe and card corrected.
  CHANGE-BRIEF gets an appended correction, and the old numbers stay.
- **[AI] added persona filters** (your-input): seniority/intern title exclusions
  and a non-US location exclusion list, so a "Staff Data Engineer" posting or a
  Bengaluru posting doesn't make a company `live` for a pre-OPT new grad.
  **[ME] accept / change (Akshit Verma):** accepted. After run-1 I extended them
  with contract / student-worker / part-time (next entry). On reflection the
  seniority exclusion fits the fictional new-grad persona, but would be wrong for
  an experienced candidate, for whom a Staff role is in scope. The patterns are
  persona inputs, so such a persona would drop them. *[AI-drafted at Akshit's request, accepted by Akshit]*
- **[ME] G1:** recorded in the next entry.

## 2026-10-03 — G1 and the live worked run (run-1)

- **[ME] G1:** I confirmed all 16 `boards.json` entries in chat. **[AI]** set
  `"confirmed": true, "confirmed_by": "Akshit Verma (G1, 2026-10-03)"` on my
  instruction (I did not edit the file myself). **How I checked (Akshit Verma, from the session record):**
  I confirmed in chat ("I confirm the boards") after the agent showed me the list.
  For the 12 Greenhouse boards, the name each board reports about itself matched the
  CSV company. The 4 Lever/Ashby boards (NerdWallet, Socure, Zoox, Cherre) have
  no self-reported name, so their confirmation rests on my judgment alone. The
  session record doesn't show me opening each board page. *[AI-drafted at Akshit's request, accepted by Akshit]*
- **[AI] ran** `--live` into `runs/run-1/`: exit 0, 16 boards fetched, scorer ran
  on 16 companies → APPLY-TAILOR 3 (Zoox, Klaviyo, Sigma Computing) · NETWORK 1
  (Outset Medical) · MANUAL-CHECK 107 · SKIP 12 (all 12 `network-blocked: funding stale`).
- **Checked [AI]:** an offline replay from `run-1/board-snapshot.json` gave identical
  buckets and counts. `pii-scan` added no new findings. Klaviyo and Outset values
  were hand-checked against the CSV row (approvals, rate, titles, funding date).
- **Wrong [found by AI on first read of run-1]:** Zoox reached APPLY-TAILOR on three
  "Contract Student Worker – Data Analyst (Part-time / 20 hrs/wk)" postings. They
  pass the title pattern and contain no excluded word. They aren't sponsorable
  full-time roles for a Dec-2026 graduate. The exclusion list was missing
  contract / student-worker / part-time.
- **Observed:** Outset Medical, the only NETWORK target, is a "data-role sponsor"
  only because of a *Staff Data Engineer* title. Its sponsorship evidence is
  senior-level, which weakens it for a new grad.

## 2026-10-03 — v0.1.1 fix and run-2

- **[ME] decided:** exclude contract / student-worker / part-time postings, and
  produce run-2 by replaying run-1's snapshot so only the rule changes (run-1 kept
  untouched). Add a senior-only-evidence **flag**, without changing buckets.
- **[AI] implemented:** the persona pattern, a `senior_only_evidence` field, the
  counter renamed `senior_or_intern_excluded` → `excluded_by_title_rule`, a
  fixture posting, and 2 new tests (25/25 pass). Recipe bumped to v0.1.1.
- **Broke during the fix:** an AI-written Python edit script failed on JSON
  backslash escaping (`AssertionError`, nothing written). Redone with direct edits.
- **run-2 result:** exactly one bucket changed (Zoox APPLY-TAILOR → SKIP). New
  measured finding: 53 of 123 candidates have senior-only data-title evidence,
  including Outset Medical (the only NETWORK target) and Sigma Computing.
- **Learned (Akshit Verma):** the tests passed and the output was still wrong. Tests only check what you thought to test. Reading the actual postings found the Zoox error. Rerunning the *same* snapshot isolated the effect of the fix. *[AI-drafted at Akshit's request, accepted by Akshit]*

## 2026-10-03 — G3, status, verification, and step 4 documents

- **[ME] signed G3** and asked to delete the synthetic `runs/fixture-demo/` folder. **[AI]** deleted it.
  Recipe status → `RUNNABLE-SAMPLE`, with `last_gate` naming my G1 and G3 sign-offs.
  `attestation` stays `null`, following the repo's `local-wage-adjustment` precedent.
- **Found [AI]:** before the CRLF fix, `npm run doctor` also reported "0/33 recipes
  carry lifecycle frontmatter". After it, 33/33. Another line-ending artifact.
- **Verified [AI]:** four failure cases (expired OPT → exit 3, nothing written;
  stale snapshot → exit 5; `--out-dir data/examples` → exit 2; no board source →
  exit 2). Live break attempt: Klaviyo mapped to its empty Ashby board →
  MANUAL-CHECK, `roles.json` empty.
- **Broke:** `npm run ats:liveness` failed on a fresh clone (Playwright browser not
  installed). **Fixed [AI]:** `npx playwright install chromium`. Then all 3
  APPLY-TAILOR URLs were reported active by the repo's own checker.
- **AI error caught in its own draft:** the first WORKED-RUN draft pasted the
  3-URL liveness command above output from the earlier 1-URL attempt ("Checking 1
  URL(s)…"), and showed comparison-script lines as if the prototype had printed
  them. Corrected before review: each command now sits above its own exact output.
- **[AI] drafted** WORKED-RUN.md (with attestation), DOMAIN-JUSTIFICATION.md,
  `logs/runs/2026fa-AkshitVerma-AV-1.md`, SOURCES.md. **[ME] review (Akshit Verma):** reviewed in chat, 2026-10-03. I asked the agent to fill the remaining `[ME]` blanks. Every such fill is marked AI-drafted.
- **[ME] G3 outreach choice (Akshit Verma, as human reviewer):** selected Outset
  Medical, the only NETWORK target, for outreach toward a senior data-engineering
  path, and judged its ⚠ senior-only evidence acceptable for that path. *[AI note:
  "Staff Data Engineer" is the title in Outset's H-1B record. Outset had no open
  data posting on 2026-10-03, so this is networking toward a future role, which is
  what the NETWORK bucket is for. The flag is persona-relative: a warning for a new
  grad, a match for an experienced candidate.]*

## 2026-10-03 — Funding rationale confirmed

- **[ME] Akshit Verma** explicitly confirmed the funding-requirement reasoning
  above (drafted by the AI at my request) as my own position.
- **[AI]** carried it into the recipe (workflow step 3), the card (Purpose) and
  DOMAIN-JUSTIFICATION.md (engine layers), each labeled as my decision and as a
  hypothesis, not a record.

## 2026-10-03 — My own verification (step 1)

- **[ME] Akshit Verma ran 7 checks myself** in the VS Code PowerShell terminal.
  The agent provided the commands and expected results; I ran them and compared.
  My result: **all matched.**
  1. CSV rows for Outset Medical, Klaviyo and Sigma Computing (read directly with
     `Import-Csv`) match the run-2 report: 44 / 95.65%, 154 / 97.47%, 136 / 100%.
  2. Scorer arithmetic in `runs/run-2/role-scores.md`: 0.315 → Apply for Klaviyo
     and Sigma; 0 → gated Skip for Outset.
  3. `runs/run-2/roles.json` holds exactly the 16 confirmed boards; only Klaviyo and
     Sigma have liveness 1.0.
  4. My own offline reproduction → `runs/my-check/` (created 19:29):
     APPLY-TAILOR 2 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 13, identical to run-2.
  5. Opened the Outset Medical and Sigma Computing Greenhouse boards in a browser.
  6. Tests: 25 OK.
  7. Break attempt (expired OPT): G0 failure, exit 3, no output folder.
- **[AI] cross-checked** that `runs/my-check/network-targets.json` exists with
  counts identical to run-2, and that `runs/should-not-exist` was never created.

## 2026-10-03 — Privacy redaction before the first commit

- **Found [AI], before committing:** drafted passages tied my real name to real
  immigration status, work history and an outreach plan. `DATA_CONTRACT.md`
  §Zero-Conditions counts these as PII ("real contact or immigration details",
  "outcomes tied to a real person", "job history").
- **[ME] Akshit Verma decided:** redact. The documents now describe the target
  situation and the fictional persona, and record my G1/G3 decisions as the human
  reviewer without personal details. Nothing had been committed, so no history
  rewrite was needed.
- **[ME] decided:** keep my university email as the git author email. **[AI]
  checked:** `pii-scan.mjs --diff` only scans added lines (`+`), not the commit
  `Author:` header, so CI won't flag it. The contract's allowed list names GitHub
  noreply addresses; I accepted that difference knowingly.

## 2026-10-03 — Clean-checkout test (step 4) → TEST-REPORT.md

- **[ME] Akshit Verma ran** the clean checkout myself: a fresh clone of `98736cc`,
  then doctor, verify, the documented `python3` command, tests, conformance, the
  expired-OPT case, the PII scan and the namespace check. All outputs are pasted in
  TEST-REPORT.md.
- **Broke [ME]:** `npm install` → `npm.ps1 cannot be loaded because running scripts
  is disabled`. **Fixed [ME]:** `Set-ExecutionPolicy -Scope Process -ExecutionPolicy
  Bypass` (session only; the agent suggested it).
- **Decided [ME]:** not to run `npm audit fix` / `npm approve-scripts`, because
  they would modify `package.json` / `package-lock.json` outside my namespaces.
- **Broke [ME]:** `npm run verify` failed on 4 repo `.sh` files in PowerShell,
  before and after my run. **Diagnosed [AI]:** in PowerShell, `bash` is the WSL
  launcher (`C:\Windows\system32\bash.exe`) and no Linux distribution is
  installed, so every `bash -n` fails. In Git Bash it passes. **[AI] confirmed**
  that `verify` passes in my clean checkout with `C:\Program Files\Git\bin` first
  on the PATH. That run is labeled as the agent's in TEST-REPORT §E2.
- **Result [ME]:** prototype counts identical to run-2; 25/25 tests; branch PII
  scan clean; 46 files, all inside my four namespaces.
- **Learned [ME, AI-drafted at Akshit's request, accepted by Akshit]:** "runs on a
  fresh clone" depends on the shell as well as the repo. On Windows, three
  environment gaps (CRLF, the PowerShell execution policy, WSL `bash`) each
  produced a failure that looked like a code problem and wasn't.

## 2026-10-03/04 — Push, PR #44, and CI

- **[ME] Akshit Verma approved** the push and asked the agent to install `gh` and
  open the PR. **[AI]** installed GitHub CLI 2.102.0 (`winget`, user scope). **[ME]**
  authorized it in the browser (device code). **[AI]** pushed the branch and opened
  https://github.com/nikbearbrown/the-reallocation-engine/pull/44 (2 commits,
  47 files, head `4eb9bd4`).
- **Found [AI]:** both workflows are `action_required`. GitHub holds CI on a
  first-time contributor's fork PR until a maintainer approves it. I can't approve
  it myself.
- **Found [AI]:** the instructor's own `main` (`015843d`, my merge base) fails
  "Contrib Gate" on every recent commit. CI logs:
  - `harness-regression`: `Cannot find module …/scripts/test/gate-behavior-harness.mjs`.
    4 of the 6 harness scripts the job calls don't exist on `main`
    (`scripts/test/gate-behavior-harness.mjs`, `scripts/test/fuzz-invariants.mjs`,
    `scripts/gates/gate-behavior-harness.mjs`, `scripts/score/scorer-harness.mjs`).
    The other 2 run and pass, but don't print the text CI greps for ("17/17
    passed", "VALID").
  - `doctor-and-pii`: the working-tree `pii-scan` stops on an email-address match in
    `package-lock.json`: the contact address inside an npm deprecation notice.
- **Checked [AI]:** every CI job replicated locally on `4eb9bd4`. verify,
  conformance, manifest-check, doctor, `pii-scan --diff`, and contrib-scope (47
  files, 0 outside namespaces, no protected paths) pass. The two failures above
  are identical to `main`'s, and my branch changes none of the files involved. CI
  green isn't reachable for any student PR until those are fixed upstream. This is
  documented in the PR description.
- **AI slip, caught before push:** the first draft of this entry quoted that
  lockfile address verbatim. The branch-history `pii-scan --diff` flagged
  FRICTIONAL.md, and because the push only runs after a clean scan, nothing was
  pushed. The unpushed commit was amended with the address described, not quoted.
