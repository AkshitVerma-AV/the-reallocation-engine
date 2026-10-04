# TEST-REPORT — preopt-data-network-targets v0.1.1

## Executive summary

I (Akshit Verma) cloned my branch fresh, at commit `98736cc`, into a separate
folder and ran the prototype, its tests, a failure case and the repo checks there,
in the VS Code PowerShell terminal on Windows 11.

- **The prototype reproduced run-2 exactly:** APPLY-TAILOR 2 · NETWORK 1 ·
  MANUAL-CHECK 107 · SKIP 13.
- **Tests:** 25/25 passed.
- **Conformance** on my folder passed.
- **The expired-OPT case** stopped at G0 with exit 3.
- **PII scan of the branch history:** clean.
- **The diff** touches only my four assigned folders.
- **`npm run doctor`** passed before and after.
- **`npm run verify`** failed before and after on four repo shell scripts my work
  doesn't touch. The cause: in PowerShell, `bash` is the WSL launcher, which has
  no Linux distribution installed. With Git's bash first on the PATH, `verify`
  passes.

I hit and solved two other Windows environment gaps along the way. They are
recorded below.

**Who ran what.** Sections A–E are my own runs; the outputs are pasted from my
terminal. The one exception is the passing `verify` with Git's bash (§E2), which
the AI agent ran in my clean checkout after diagnosing the failure. It is labeled
as such.

## Environment

Windows 11 Home · PowerShell 5.1 (VS Code terminal) · Node v24.19.0 · Python
3.12.10 · Git 2.46.0 (Git for Windows) · Playwright installed · pandoc and
libreoffice not installed (optional, not used by this recipe).

## A. Clean checkout

```powershell
cd "C:\Users\Akshit Verma\PromptEngr\Assignment_1"
git clone -c core.autocrlf=false --branch contrib/2026fa-AkshitVerma-AV-preopt-data-network-targets the-reallocation-engine clean-check
cd clean-check
git log --oneline -1
npm install
```

```text
98736cc (HEAD -> contrib/2026fa-AkshitVerma-AV-preopt-data-network-targets, origin/contrib/2026fa-AkshitVerma-AV-preopt-data-network-targets, origin/HEAD) contrib(2026fa): pre-OPT data network-targets recipe + prototype (RUNNABLE-SAMPLE)
npm : File C:\Program Files\nodejs\npm.ps1 cannot be loaded 
because running scripts is disabled on this system. For more 
information, see about_Execution_Policies at 
https:/go.microsoft.com/fwlink/?LinkID=135170.
```

**Fix (mine):** `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
(this terminal session only), then `npm install`:

```text
up to date, audited 54 packages in 4s

16 packages are looking for funding
  run `npm fund` for details

3 high severity vulnerabilities

To address issues that do not require attention, run:
  npm audit fix

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.
npm warn allow-scripts 1 package has install scripts not yet covered by allowScripts:
npm warn allow-scripts   sharp@0.33.5 (install: node install/check)
npm warn allow-scripts
npm warn allow-scripts Run `npm approve-scripts --allow-scripts-pending` to review, or `npm approve-scripts <pkg>` to allow.
```

I deliberately did **not** run `npm audit fix` or `npm approve-scripts`. Both
would modify `package.json` / `package-lock.json`, which are outside my
namespaces. The vulnerabilities are in the repo's existing dependencies; my
prototype uses only the Python standard library. Afterwards, `git status` in the
clean checkout showed only my new run folder (`runs/clean-check/`), so no
tracked file changed.

`-c core.autocrlf=false` on the clone avoids a third Windows gap, found earlier
on my working clone. With Git for Windows' default CRLF checkout, `npm run verify`
fails with 6× `E3 … out of sync` on the generated adapter files
(FRICTIONAL.md, 2026-10-03).

## B. Toolchain baseline, before

```text
> the-reallocation-engine@1.0.0 doctor
> node scripts/doctor.mjs

RECIPE DOCTOR — The Reallocation Engine
==========================================

ENVIRONMENT (required)
  ✓ node       v24.19.0
  ✓ python3    Python 3.12.10

ENVIRONMENT (optional — features degrade without these)
  — pandoc     not found (resume/PDF rendering)
  — libreoffice not found (PDF fallback)
  ✓ playwright installed

RUNNABLE COMMANDS (npm script → target file present?)
  ✓ verify         scripts/conformance.mjs
  ✓ manifest-check scripts/manifest-check.mjs
  ✓ eval:score     scripts/eval/score-run.mjs
  ✓ eval:report    scripts/eval/report.mjs
  ✓ doctor         scripts/doctor.mjs
  ✓ bls:local-wage scripts/bls/local-wage-adjustment.py
  ✓ build-instructions scripts/build-instructions.mjs
  ✓ to-markdown    scripts/to-markdown.mjs
  ✓ score          scripts/score/role-scorer.mjs
  ✓ score:gates    scripts/score/gate-harness.mjs
  ✓ ats:dedup      scripts/ats/dedup-tracker.mjs
  ✓ ats:liveness   scripts/ats/check-liveness.mjs
  ✓ ats:merge      scripts/ats/merge-tracker.mjs
  ✓ ats:normalize  scripts/ats/normalize-statuses.mjs
  ✓ ats:scan       scripts/ats/scan.mjs
  ✓ ats:verify     scripts/ats/verify-pipeline.mjs
  ✓ resumes:pdf    scripts/resumes/generate-pdf.mjs
  ✓ svg-to-png     scripts/svg-to-png.mjs
  ✓ audit:layout   scripts/svg-layout-audit.mjs
  ✓ postsvg-to-png scripts/svg-layout-audit.mjs
  ✓ skill-demand   scripts/score/skill-demand-monitor.mjs
  ✓ skill-demand:test scripts/score/skill-demand-monitor.test.mjs
  ✓ fetch-postings scripts/ats/fetch-real-postings.py
  ✓ pii-scan       scripts/pii-scan.mjs

DOMAIN DIRECTORIES
  ✓ data/sec
  ✓ data/bls
  ✓ data/ats
  ✓ data/80-days-to-stay
  ✓ scripts/sec
  ✓ scripts/bls
  ✓ scripts/ats
  ✓ scripts/resumes

PRIVACY (no personal data committed)
  ✓ no private/PII paths are tracked

RECIPES (33)
  with lifecycle frontmatter: 33   missing: 0
  by status: DRAFT 28 · RUNNABLE-SAMPLE 4 · RUNNABLE-LIVE  # DRAFT | SPECIFIED | RUNNABLE-SAMPLE | RUNNABLE-LIVE | VERIFIED 1
  open TODOs: 318 declared (in frontmatter) · 318 [TODO markers in bodies

SUMMARY
  environment: ✓ runnable
  recipes: 33/33 carry lifecycle frontmatter — all tracked
  next: continue

> the-reallocation-engine@1.0.0 verify
> node scripts/conformance.mjs && node scripts/manifest-check.mjs

conformance: 168 files (88 md · 38 py · 30 js · 8 json · 4 sh)

✗ 4 file(s) FAILED conformance:
  • scripts\fetch\fetch-oews.sh — failed
  • scripts\fetch\fetch-onet.sh — failed
  • scripts\gitignore-large.sh — failed
  • scripts\run-real-demo.sh — failed
```

The four failing files are repo scripts, none of them mine, and they fail
*before* my prototype runs. The cause is diagnosed in §E2.

## C. The sample run, using the documented README command

```powershell
python3 scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json --as-of 2026-10-03 --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/clean-check
```

```text
✓ scored 16 roles → Apply 2 · Consider 0 · Skip 14 (skip 88%)
  course\2026fa\submissions\AkshitVerma-AV\runs\clean-check\role-scores.json  +  course\2026fa\submissions\AkshitVerma-AV\runs\clean-check\role-scores.md
✓ 123 candidates → APPLY-TAILOR 2 · NETWORK 1 · MANUAL-CHECK 107 · SKIP 13 (network-blocked 13)
  course\2026fa\submissions\AkshitVerma-AV\runs\clean-check\network-targets.json  +  network-targets.md
```

These are identical to the committed `runs/run-2` counts. The output folder lives
only in the throwaway clean checkout and is not committed.

## D. Tests, conformance, and a failure case

```powershell
python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets -p "test_*.py"
node scripts/conformance.mjs scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/
python3 scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-expired-opt.json --boards scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json --as-of 2026-10-03 --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/should-not-exist
$LASTEXITCODE
```

```text
>> 
.........................
----------------------------------------------------------------------
Ran 25 tests in 2.139s

OK
conformance: 8 files (5 json · 2 py · 1 md)
✓ all conform (machine half of P4). Adequacy is still the human gate.
✗ G0 failed: opt_end_date 2026-05-31 is not after as_of 2026-10-03 — OPT window already closed
3
```

## E. After

### E1. My run (PowerShell, default PATH)

`npm run doctor`: identical to §B (environment runnable, no tracked PII paths).
`npm run verify`: the same four `.sh` failures as §B. Then:

```powershell
node scripts/pii-scan.mjs --diff origin/main
git diff --stat origin/main...HEAD | Select-Object -Last 1
git diff --name-only origin/main...HEAD | ForEach-Object { ($_ -split '/')[0..1] -join '/' } | Sort-Object -Unique
```

```text
pii-scan: clean ✓
 46 files changed, 84934 insertions(+)
course/2026fa
logs/runs
recipes/cases
scripts/contrib
```

### E2. The `verify` failure: diagnosis and passing run (run by the AI agent in my clean checkout)

`conformance.mjs` syntax-checks shell files with `bash -n`. In PowerShell, `bash`
resolves to the Windows Subsystem for Linux launcher, which has no Linux
distribution installed here. Output of `Get-Command bash -All` and `bash -n
scripts/run-real-demo.sh`. The WSL message actually printed first, in UTF-16
(`W i n d o w s   S u b s y s t e m …`), and is re-spaced and reordered here
for readability:

```text
Source
------
C:\Windows\system32\bash.exe
C:\Users\Akshit Verma\AppData\Local\Microsoft\WindowsApps\bash.exe

Windows Subsystem for Linux has no installed distributions.
```

With Git's bash first on the PATH, in the same clean checkout:

```powershell
$env:Path = "C:\Program Files\Git\bin;" + $env:Path
npm.cmd run verify
```

```text
> the-reallocation-engine@1.0.0 verify
> node scripts/conformance.mjs && node scripts/manifest-check.mjs

conformance: 168 files (88 md · 38 py · 30 js · 8 json · 4 sh)
✓ all conform (machine half of P4). Adequacy is still the human gate.
MANIFEST CHECK — The Reallocation Engine
==========================================

WARN (3):
  W1 ignore path not in .gitignore: archive/
  W2 private path not gitignored (PII/secret risk): private/
  W2 private path not gitignored (PII/secret risk): data/ats/

✓ manifest check passed (3 warnings)
```

The W2 warnings are false positives. `git check-ignore -v` shows `/private/*` and
`/data/ats/*` are ignored; the manifest check only looks for the literal string
`private/` (FRICTIONAL.md).

## Failure cases from CHANGE-BRIEF §4: where each was exercised

| # | Case | Exercised by | Result |
|---|---|---|---|
| 1 | Company missing from the CSV | `test_company_not_in_csv_is_never_scored` | listed in `board_map_unmatched`, never scored, never `p = 0` |
| 2 | Board 404 / wrong slug | `test_404_is_unresolved`; live break (Klaviyo → empty Ashby board, WORKED-RUN §5) | `unresolved` → MANUAL-CHECK, never sent to the scorer |
| 3 | SOC code with no row | `test_soc_with_no_row_is_missing_not_invented` | `status: missing`, no wage field |
| 4 | OPT date already past | §D above (my run); `test_expired_opt_stops_at_g0_and_writes_nothing` | exit 3, nothing written |
| 5 | Title regex errors | `TitlePatterns` tests (true +/−, borderline, a known false negative pinned) | documented behavior |
| — | Not predicted: contract/student-worker postings | `test_contract_student_worker_posting_does_not_count_as_live` (v0.1.1) | excluded |

## What the gates require a human to judge

- **G1:** that each `boards.json` entry is the same company as its CSV row. The
  Greenhouse API reports a board name to compare against; Lever and Ashby don't,
  so those four rest on human judgment alone.
- **G2:** reading `unresolved` as "unknown", never as "nothing open".
- **G3:** whom to contact from the NETWORK list, weighing flags the machine can't
  settle (⚠ senior-only evidence, whether recent funding means hiring).

## Not covered by this report

macOS/Linux; a `--live` run from the clean checkout (it used the committed
snapshot so the result is comparable); Git Bash as the terminal for the whole
sequence.
