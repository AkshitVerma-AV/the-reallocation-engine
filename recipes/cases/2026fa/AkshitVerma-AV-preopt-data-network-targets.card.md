# Pre-OPT data network targets — human card

**Audience:** an F-1 MSIS student who hasn't started OPT yet and is deciding where
to spend networking hours versus application hours on Data Analyst / Data Engineer roles.
**Agent twin:** `recipes/cases/2026fa/AkshitVerma-AV-preopt-data-network-targets.md`
**Chapters:** 7 (who sponsors), 8 (is the posting live), 11 (the scorer). Persona: fictional (Jack Spencer, Chicago).

## Purpose

Answer: *which companies with a record of sponsoring data roles, and recent
funding, have nothing open right now, so I should network into them before a role
opens, not apply?* If the
evidence can't support a bucket, the company goes to `MANUAL-CHECK` with a reason.
It is never guessed into a bucket.

**Why recent funding is required** (my decision): networking pays off over weeks,
so I want it aimed at companies likely to be adding data headcount before the
persona's OPT starts. A recent raise is the engine's only forward-looking signal. It's a
hypothesis, not a record, and it costs a lot on the shipped samples (1 target, 13
strong sponsors blocked and listed). Better data is the fix, not a looser window.

## What it can verify

- The 80 Days CSV row: H-1B approvals, denials, approval rate, and the top sponsored job titles.
- That one of those titles matches a data-role pattern.
- What the company's public Greenhouse / Lever / Ashby board returned at a stated time: status, total postings, matching postings.
- Whether the company appears in one of the four shipped Form D **samples**.
- The national BLS median wage for the parent codes 15-2051 and 15-1243.
- The existing scorer's decision and its per-term trace.

## What it cannot verify

- That the sponsorship evidence is entry-level. 53 of 123 candidates qualify only through senior data titles; the report marks these `⚠ senior-only data-title evidence` without changing their bucket.
- That the company sponsors **data** roles, **new grads**, or sponsors **today**. Approvals are company-wide and backward-looking.
- That the CSV company and the ATS board are the same company. You confirm this.
- That "no data posting on this board" means "not hiring" (other ATSs, recruiters, next week).
- That a listed posting is not a ghost posting.
- That a company with no funding evidence is unfunded. Recent funding is **required** for NETWORK, but only 3 of 123 candidates have a funding date in the last 24 months, and the Form D samples cover 200 companies. On a fresh clone, at most 2 companies can reach NETWORK. Strong sponsors blocked only by funding are counted in the report under `network-blocked`.
- Chicago pay. The wage is national.
- Fit. Not scored. You read the posting.

## Dependencies

- Node 20+ (for `scripts/score/role-scorer.mjs`), Python 3 (standard library only, no venv).
- `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv`
- `data/sec/form-d/processed/sample/*.sample.json`
- `data/bls/compact/soc_occupation_compact.csv`
- `scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json`: you fill this in and set `"confirmed": true` per company.

## Annotated commands

Live board check (calls only the Greenhouse / Lever / Ashby APIs):

```bash
python3 scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py \
  --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json \
  --boards  scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json \
  --live --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/run-1
```

Offline replay (no network; expected to give identical buckets for the same snapshot):

```bash
python3 .../network_targets.py --persona ... --boards ... \
  --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json \
  --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/replay
```

Expired OPT (expected: exit 3, names the failed date, writes nothing):

```bash
python3 .../network_targets.py --persona .../fixtures/persona-expired-opt.json --boards ... --snapshot ... --out-dir /tmp/x
```

## What it produces

- `network-targets.md`: for you. Counts per bucket, then one table per bucket. Every value is tagged `[record]`, `[your-input]` or `[model-judgment]`.
- `network-targets.json`: for an agent. The same content as structured fields.
- `role-scores.{json,md}`: the existing scorer's own output, untouched.

## What you decide (gates)

- **G1:** before any board is fetched, confirm that each `boards.json` entry is the same company as its CSV row.
- **G2:** treat `unresolved` as "I don't know", not as "nothing open."
- **G3:** choose which `NETWORK` companies to contact. The recipe sends nothing.

## Named failure modes

1. **Name-collision false target.** A generic CSV name (e.g. `HUMAN INC`) is mapped to a different company's board. Its "no data posting" result is real, but for the wrong company, so you end up networking into a firm with no sponsorship record. Hardest to catch for a student who doesn't know the industry. Mitigation: `"confirmed": true` at G1, and the website is shown next to every row.
2. **Moved-ATS false target.** A company leaves Greenhouse, and the old board returns zero postings. Read as `none`, it would become a NETWORK target while the company is actively hiring elsewhere, and the student would lose the application window. Mitigation: zero postings total is `unresolved`, not `none`.
3. **Funding-gap exclusion.** A strong data-role sponsor that raised money last quarter, but isn't in the four Form D samples and has an old CSV funding date, is blocked from NETWORK. A student reading only the NETWORK table would never see it. Mitigation: the `network-blocked` count and list in the report. The fix is [TODO: DATA SOURCE] full Form D quarters.
4. **Top-N title blind spot.** A large employer that sponsored many data engineers, but whose top titles are all software roles, never becomes a candidate. This is a silent false negative, and it is invisible in the output by construction. Mitigation: documented here only. The fix is [TODO: DATA SOURCE] title-level LCA data.
