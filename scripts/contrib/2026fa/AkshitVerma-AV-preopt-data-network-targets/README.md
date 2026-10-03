---
owner: AkshitVerma-AV
term: 2026fa
component: preopt-data-network-targets
status: RUNNABLE-SAMPLE
promoted_to: null
---

# preopt-data-network-targets — prototype

## Executive summary

This prototype runs the recipe
`recipes/cases/2026fa/AkshitVerma-AV-preopt-data-network-targets.md` end to end.

It takes companies in the 80 Days CSV with an H-1B record and a data title among
their top sponsored titles. It checks each confirmed company's public ATS board,
sends the evidence through the **existing** scorer (`scripts/score/role-scorer.mjs`,
called and not copied), and buckets each company as `APPLY-TAILOR`, `NETWORK`,
`MANUAL-CHECK` or `SKIP`. Every value is labeled `record`, `your-input` or
`model-judgment`.

The persona (Jack Spencer) is fictional. The prototype uses the Python 3 standard
library only, with no venv or pip install. Node 20+ runs the scorer.

## Run (one command, from the repo root)

Offline, using the saved snapshot from the worked run. No network:

```bash
python3 scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/network_targets.py \
  --persona scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/fixtures/persona-jack-spencer.json \
  --boards  scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets/boards.json \
  --snapshot course/2026fa/submissions/AkshitVerma-AV/runs/run-1/board-snapshot.json \
  --as-of 2026-10-03 \
  --out-dir course/2026fa/submissions/AkshitVerma-AV/runs/replay
```

Live: replace `--snapshot …` and `--as-of …` with `--live`. This calls only
`boards-api.greenhouse.io`, `api.lever.co` and `api.ashbyhq.com`, one GET per
confirmed board.

On Windows, `python` works in place of `python3`.

## Test (offline, uses fixtures, no network)

```bash
python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets -p "test_*.py" -v
```

The test patches `urllib.request.urlopen` to raise, so any network call fails the
test. It reads the real repo CSV, Form D samples and BLS file, and runs the real
scorer through `node`.

## Files

| File | What | Label |
|---|---|---|
| `network_targets.py` | the prototype | — |
| `test_network_targets.py` | offline tests | — |
| `boards.json` | company → ATS board map; a human sets `"confirmed": true` per entry (G1) | your-input |
| `fixtures/persona-jack-spencer.json` | fictional persona: dates, title patterns, exclusions | your-input |
| `fixtures/persona-expired-opt.json` | failure case: OPT already ended, so G0 exits 3 | your-input |
| `fixtures/boards-fixture.json`, `fixtures/board-snapshot-fixture.json` | test fixtures. Postings are **synthetic** (example.com URLs) | fixture |

## Exit codes

`0` ok · `2` usage/input error, or `--out-dir` outside this contribution's
namespaces · `3` G0 timeline failed (nothing written) · `4` zero candidates ·
`5` snapshot older than 7 days · `6` scorer failed.

## Outputs (all written into `--out-dir`)

- `network-targets.json` (agent) and `network-targets.md` (person)
- `candidates.json`, `board-snapshot.json`, `roles.json`
- `role-scores.json` and `role-scores.md` (the scorer's own output)

The CSV's phone, executive and board-director columns are never copied out.
