# Mode Build submission — Akshit Verma (AkshitVerma-AV)

## Executive summary

This folder is my Mode Build Assignment submission for The Reallocation Engine.
The mode tells an F-1 data-role job seeker how many wage-weighted H-1B lottery
entries a posting's pay, or an offer, could earn. It works that out under every
job code the employer could plausibly file, and it refuses to guess where the
data runs out. It ran live on 2026-10-19 against 16 company job boards. The
honest stage it reached is **RUNNABLE-SAMPLE**: real data and real runs, but a
fictional persona, hypothetical offers, and a national wage ladder standing in
for the local one.

## Where everything is

| Deliverable | Path |
|---|---|
| Mode file (recipe, agent-facing) | `recipes/cases/2026fa/AkshitVerma-AV-data-lottery-weight.md` |
| Human card | `recipes/cases/2026fa/AkshitVerma-AV-data-lottery-weight.card.md` |
| Domain justification (≤ 1 page) | `DOMAIN-JUSTIFICATION.md` |
| Worked run + verification + attestation + reflection | `WORKED-RUN.md` |
| Run log entry | `logs/runs/2026fa-AkshitVerma-AV-2.md` |
| Sources and AI use | `SOURCES.md` |
| Honest work log (who did what, what broke) | `FRICTIONAL.md` |
| Presentation talk track | `PRESENTATION-NOTES.md` |
| Prototype, tests, fixtures, mutants | `scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/` |
| Run outputs | `runs/` (engine-baseline, run-0-crash … run-5-replay, verification) |

## Path note

The assignment text names `recipes/` and `assignments/submissions/<name>/`.
This repo's Fall 2026 `CONTRIBUTING.md` (enforced by the Contrib Gate CI)
requires `recipes/cases/<term>/` and `course/<term>/submissions/<handle>/`, and
forbids editing `logs/RUN_LOG.md`, so the run log is under `logs/runs/`. I
followed the CI-enforced layout. This folder is `mode-build/` so it can't
collide with my Assignment 1 files from PR #44.
