# Domain justification — data-lottery-weight

## Executive summary

Who this mode is for, what it shows them that they can't easily see, how it
connects to the engine, and the two domain mistakes hardest to catch. In short,
the H-1B lottery now rewards higher wage steps, and for a data student the step
depends mostly on a job code the student never sees.

## Who, and in what exact situation

An international MS Information Systems student on F-1, graduating December 2026,
with OPT from late January 2027. They are applying for Data Analyst, BI, Analytics
Engineer and Data Engineer roles at cap-subject employers. Their first realistic
H-1B registration is FY2028, in about March 2027, and the employer needs an
accepted offer before then. STEM OPT gives two more tries; without it they get
one. That is my situation, run on a fictional stand-in (Jack Spencer) so no
personal data enters the repo.

## The information asymmetry

Since FY2027, USCIS weights the lottery by wage level: Level I gets one entry,
Level IV four (90 FR 60864, effective 2026-02-27). The level depends on:

1. **the offered wage**, which the student sees only as a posted range;
2. **the SOC code on the LCA**, chosen by the employer's counsel *after* the offer;
3. **the worksite's prevailing wage**, in an OFLC table most students don't know exists.

For data titles the SOC choice is enormous. O*NET lists the exact title "Data
Analyst" under **seven** occupations. On the national ladder the same $85,000 is
at or below Level I as a Database Architect (15-1243), I–II as a Data Scientist
(15-2051), and III–IV as a Market Research Analyst (13-1161): one to four entries
for one salary. The employer and its lawyer see that spread; the student doesn't.
The mode makes it visible per posting and per offer, and turns it into one question
for the recruiter: *which SOC code and wage level will the LCA use?*

## Connection to the engine

- **80 Days to Stay:** H-1B approvals and approval rate set the sponsorship tier.
- **Job-Ops:** public ATS board APIs supply the liveness gate and the posted pay; `npm run ats:liveness` cross-checks.
- **Cognitive Pivot / BLS:** the national OEWS ladder and O*NET alternate titles supply the wage steps and plausible SOCs.
- **Decision core:** `scripts/score/role-scorer.mjs` is called, not copied; the lottery read sits beside its recommendation, never inside it.

## Failure modes specific to this domain

**1. Reading the optimistic code.** A student finds "Data Analyst" under Market
Research Analysts on O*NET and concludes $85,000 is Level III. The employer files
under Data Scientists or Database Architects, and the registration carries one
entry. The error always flatters the offer, and it surfaces only after the offer is
signed. **Who struggles most to catch it:** a first-job data analyst at a company
with no in-house immigration team, where nobody knows the SOC until outside counsel
files. The mode reads every plausible code and reports the worst case.

**2. Comparing a data offer to the company's median sponsored salary.** The 80 Days
column `median_salary_offered` sounds like "what this company pays sponsored hires",
but it is a company-wide median across all titles, mostly software engineers.
Klaviyo's is $126,000; its Analytics Engineer floor is $112,000. "Below the median,
so Level I" and "near the median, so fine" are both meaningless. **Who struggles
most:** anyone at a software-heavy sponsor, because the column name carries no
title qualifier. The mode shows it only as labeled context and never compares it.
