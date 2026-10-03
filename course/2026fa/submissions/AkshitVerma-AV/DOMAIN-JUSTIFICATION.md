# Domain justification — pre-OPT Data Analyst / Data Engineer network targets

## Executive summary

This recipe is for an international MSIS student on F-1 who hasn't started OPT
and wants Data Analyst or Data Engineer work. It shows which H-1B sponsors of
data roles have **no** open role right now, and are therefore worth
networking into before a role opens. It takes over the company-research part
of the daily two "apply" hours and feeds the three networking hours.

## Who, in exactly what situation

An MS Information Systems student (a STEM-designated program) on F-1,
graduating in December, with an EAD start in late January. They target Data
Analyst (O*NET 15-2051.01) and Data Engineer (15-1243.01) roles, and will need
H-1B sponsorship once OPT runs out. They can't start work for about four months,
so most postings open today will be filled by someone who can start sooner.
Their best use of the gap is relationships at the right companies.

## The information asymmetry

From outside, the student can't easily see **which employers have actually
sponsored *data* roles, and which of those have nothing posted for a new grad
today**. A careers page shows what's open, not who sponsors. H-1B data shows who
sponsored, not what's open. Neither says whether the sponsorship evidence is
entry-level. On the shipped data, **53 of 123** data-title sponsors (43%) qualify
only through senior titles such as "Staff Data Engineer". A student who reads
"Proven sponsor" as "sponsors people like me" is misled.

## Engine layers

- **80 Days to Stay** (sponsorship record, top sponsored titles, CSV funding dates).
- **SEC Form D samples** (funding recency). It's a NETWORK requirement by my
  choice, because a recent raise is the only forward-looking hiring signal in the
  engine. That's a hypothesis, and on the shipped samples it costs 13 blocked
  sponsors, all listed in the report.
- **Job-Ops** (public Greenhouse / Lever / Ashby board APIs, cross-checked with
  `ats:liveness`).
- **Cognitive Pivot** (national BLS medians, as context only, because the
  `role_quality` weight is 0.0).
- **The decision** is made by the existing `scripts/score/role-scorer.mjs`.

## Where it fits the 3-3-2 day

It takes over the **research half of the 2 hours**: checking, company by
company, "do they sponsor data roles? Is anything open for me? Did they raise
money recently?" By hand I'd budget about 15–20 minutes per company (H-1B
lookup, careers page, funding search).

**Estimate, not measured:** checking about 20 companies a week by hand is 5–7
hours. The recipe does the record lookups for all 123 candidates and the board
checks for every confirmed board in one command. What's left is roughly an hour
a week: confirming new boards at G1, reading the report, and the MANUAL-CHECK
lookups. That saves an estimated **4–6 hours a week**, which is most of the
10-hour weekly "2" budget.

The output feeds the **networking 3** directly: the NETWORK list is an outreach
list. The recipe and prototype themselves, with their tests and honest limits,
are a piece of work for the **credibility 3**.

## Failure modes specific to this domain

1. **Senior-only sponsorship read as new-grad sponsorship.** A company "proves"
   it sponsors data roles through a Staff or Director data title, and the
   student networks into it, expecting a new-grad sponsorship path that the
   record never showed. This is hardest to catch for exactly this user: a pre-OPT
   student has no hiring-side experience to tell a staff-level LCA from a
   new-grad one, and the tier label looks authoritative. Mitigation: a
   `⚠ senior-only` flag (record + your-input). It's a flag only, so the human
   must still weigh it.
2. **An empty or moved board read as "no openings".** A company migrates its job
   board, and the old board answers HTTP 200 with zero postings. Read as "nothing
   open", it would become a NETWORK target, and the student would spend weeks on
   informational interviews while the company hires through its new board. The
   student finds out only after the role closes. Hardest to catch for anyone
   trusting the list without opening the careers page. Mitigation: zero postings
   total is `unresolved` → MANUAL-CHECK. A live break attempt (Klaviyo's empty
   Ashby board) confirmed it.
