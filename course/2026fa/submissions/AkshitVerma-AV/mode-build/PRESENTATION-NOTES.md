# Show-and-tell notes — 5 minutes

## Executive summary

A five-minute talk track for presenting the lottery-weight mode in class. It
covers the four things the rubric asks for: the situation, the information gap,
one lesson from running it, and one honest limit. Each beat says what to say and
what to show on screen. No slides; show the files and one live command.

## Beats

| Time | Say | Show |
|---|---|---|
| 0:00–0:45 · **Situation** | "I'm an F-1 MSIS student. OPT starts in January; my first H-1B shot is March 2027. Since last spring the lottery is wage-weighted: Level I gets one entry, Level IV gets four." | `runs/run-4-live/lottery-weight.md` → "Your lottery rounds" table (3 reachable rounds; FY2031 not) |
| 0:45–2:00 · **Asymmetry** | "The level depends on a job code the employer's lawyer picks after the offer. O*NET lists 'Data Analyst' under seven occupations. The same $85,000 is 1 entry under one code and up to 4 under another. The employer sees that spread; I don't." | the offer-A SOC table (15-1243 · 15-2051 · 15-2041 · 13-1161) |
| 2:00–3:15 · **It ran** | "16 confirmed boards, 1,264 postings, 20 data titles, 3 entry-eligible. Sigma's Data Engineer clears Level II under every code. Klaviyo's floor is $590 under the Data Scientists median, so the national data can't settle it, and the mode says so instead of guessing." | run the replay live (`--snapshot runs/run-4-live/board-snapshot.json --as-of 2026-10-19`; it took 1.7 s on my laptop), then the Postings table |
| 3:15–4:15 · **What I learned** | "Every test passed while one rule was wrong. I had scored below-Level-I wages as zero entries. Reading the rule summary showed they can still be registered once with an alternative wage survey. Tests check code against my reading; only the source check caught it. The replay also caught a timezone bug and HR emails in stored data." | `WORKED-RUN.md` → "Broke during testing, fixed" |
| 4:15–5:00 · **Limit** | "It uses the national wage ladder. The worksite table isn't in the repo, and Boston, New York and SF run higher, so these reads are likely too generous exactly where these jobs are. Next step: ingest the OFLC 2026–27 table." | recipe → "What it can and cannot verify" |

## If asked

- *Why not compute odds?* No published count of registrations by wage level was found, so entries are not odds.
- *Why the floor, not the midpoint?* An offer can land at the floor, and USCIS reportedly uses the lowest applicable level for multiple worksites.
- *Who chose the job codes?* O*NET records, plus four labeled judgments. I signed that gate (G3) after run-1 held.
