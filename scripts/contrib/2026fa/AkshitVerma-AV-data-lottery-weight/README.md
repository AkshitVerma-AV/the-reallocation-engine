---
owner: AkshitVerma-AV
term: 2026fa
component: data-lottery-weight
status: RUNNABLE-SAMPLE
promoted_to: null
---

# data-lottery-weight — prototype

## Executive summary

A small standard-library Python tool. It checks open data-analyst and
data-engineer postings at strong H-1B sponsors, reads their published pay, and
shows how many wage-weighted lottery entries that pay could earn. The answer
is a range, worked out under every job code the employer could plausibly file.
It also accepts offers you type in. It found 3 eligible postings on its first
real run, and it refuses to guess wherever the data runs out.

Recipe: `recipes/cases/2026fa/AkshitVerma-AV-data-lottery-weight.md` (agent) ·
card: `…/AkshitVerma-AV-data-lottery-weight.card.md` (human).

## Files

| File | What |
|---|---|
| `lottery_weight.py` | the mode: G0 timeline → G1/G2 boards → pay evidence → G3 SOC map → OEWS bracket → `role-scorer.mjs` → `lottery-weight.{json,md}` |
| `soc-map.json` | G3: title family → plausible SOC codes (`record` = O*NET lists the title there; `your-input` = human judgment with a reason) |
| `boards.json` | G1: 16 human-confirmed company → ATS board entries |
| `verify_runs.py` | cross-checks a live run against its replay and against independent repo sources |
| `test_lottery_weight.py` | 34 offline tests (real OEWS file, real scorer) |
| `fixtures/BROKEN-mutants.py` | 3 planted bugs; each must be caught by the tests |
| `fixtures/persona-*.json`, `offers-scenario.json`, `board-snapshot-fixture.json`, `boards-fixture.json` | fictional or synthetic inputs, all labeled |

## Run

From the repo root (Python 3.12+, Node 20+; no installs):

```bash
P=scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight
python3 $P/lottery_weight.py --persona $P/fixtures/persona-jack-spencer.json --soc-map $P/soc-map.json \
  --boards $P/boards.json --live --offers $P/fixtures/offers-scenario.json \
  --out-dir course/2026fa/submissions/AkshitVerma-AV/mode-build/runs/my-run
python3 -m unittest discover -s $P -p "test_*.py"
python3 $P/fixtures/BROKEN-mutants.py
```

Offline replay: replace `--live` with `--snapshot <run>/board-snapshot.json --as-of <date of the fetch>`.

Exit codes: 0 ok · 2 usage/input · 3 G0 (no reachable lottery window) · 4 OEWS
conformance · 5 stale snapshot · 6 scorer failed.

Network hosts (only with `--live`): `boards-api.greenhouse.io`, `api.lever.co`,
`api.ashbyhq.com`. Stored snapshots have contact emails and phone numbers redacted.
