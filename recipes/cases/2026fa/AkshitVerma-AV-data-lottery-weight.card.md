# Data-job lottery weight — human card

**Audience:** an F-1 MS Information Systems student who hasn't started OPT yet
and is choosing between, or negotiating, Data Analyst / BI / Analytics Engineer /
Data Engineer roles before the next H-1B registration window.
**Agent twin:** `recipes/cases/2026fa/AkshitVerma-AV-data-lottery-weight.md`
**Chapters:** 7 (who sponsors), 8 (is the posting live), 9 (role quality: OEWS), 10 (timeline), 11 (the scorer).
Persona: fictional (Jack Spencer).

## Executive summary

Since spring 2026, an H-1B registration gets 1 to 4 lottery entries depending
on where the offered salary sits on a four-step wage ladder. The step depends
on the job code the employer files and on local wages, and you see neither.
This card tells you how to read the report that brackets your postings and
offers against the national ladder, under every job code the employer could
plausibly use. In the first run, two Data Engineer postings cleared the second
step under every code. One Analytics Engineer posting could not be settled. A
hypothetical $85,000 Data Analyst offer ranged from 1 to 4 entries depending
only on the code.

## Purpose

Answer: *at the pay this employer posted or offered, how many lottery entries
could my registration carry, and what question should I ask before I negotiate?*
If the evidence can't support an answer, the row says `MANUAL-CHECK` and why. It
is never guessed.

## What you must decide (your gates)

- **G1: Which boards belong to which company.** Confirm each `boards.json` entry.
- **G3: Which job codes are plausible for each title.** Confirm `soc-map.json`.
  Codes marked `record` are where O*NET lists that exact title; `your-input`
  codes are a human's judgment with a reason. Prune codes that don't fit.
- **G4: Release.** Read the report, check every quoted pay sentence against the
  posting, sign.

The machine decides G0 (whether any lottery round is reachable before your work
permission ends) and G2 (whether the posting is live). Both are gates: a "no"
stops the row, whatever else is true.

## How to read a row

| You see | It means | Do this |
|---|---|---|
| **CLEARS-LEVEL-II** | the posted minimum reaches step II or higher under every plausible code (national ladder) | worth an application if the scorer agrees |
| **SOC-SENSITIVE** | the job code alone decides 1 entry vs 2+ | ask: *"Which SOC code and wage level would the LCA use for this role?"* |
| **BRACKET-UNRESOLVED** | the national data can't tell step I from step II at this pay | look up the worksite in the OFLC wage table before negotiating |
| **LEVEL-I-AT-BEST** | one entry at most at this pay | negotiate above the next published percentile, or accept single-entry odds |
| "may sit below Level I" | under some plausible code, the employer could register this wage only with an alternative wage survey, and it counts once | raise it with the recruiter early |

## What it can verify

- What the company's public job board said at a stated time: open or not, and its published pay range.
- The company's H-1B approval history (company-wide) from 80 Days.
- The national 2024 wage percentiles for each plausible code, and which interval your pay falls in.
- That O*NET lists "Data Analyst" under 7 different occupations.

## What it can't verify

- Your worksite's real wage step (the government's local table isn't in the repo). In expensive cities, the steps shown are likely too generous.
- The job code that will actually be filed.
- Your odds. Entries are not odds.
- Whether the employer uses E-Verify (needed for the STEM extension that gives you rounds 2 and 3).
- Your fit for the role.

## Never

- Never read the company's median sponsored salary as the pay for a data role. It covers every title, mostly software engineers.
- Never type a real offer for a real person into a tracked file. Real offers and their reports go in `private/`.
