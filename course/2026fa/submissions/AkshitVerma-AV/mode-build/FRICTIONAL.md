# FRICTIONAL — honest work log, Mode Build

## Executive summary

A log of what was tried while building the lottery-weight mode: what was expected,
what actually happened, what was checked and changed, and who did it, me (Akshit)
or the AI agent (Claude Code, Opus 5.5). Lines marked **[ME]** are my decisions or
words. Lines marked **[AI]** are work the agent did. The agent assembled these
entries from the session record at my request on 2026-10-21. I wrote the
reflections and every "Learned" line myself.

## My reflections [ME]

I would like to reflect on this project and say that I learned that an item that seems to be done or correct, isn't necessarily done or correct. I thought that a script in the repo should work and it turned out that it relies on data from another folks PR that hasn't been merged. I was running it early and it's the only reason I noticed that. So when I measured the data, I realised that one job title corresponded to seven occupations, and that the salary field was company-wide, so the lottery weight depends on a classification someone else picks rather than being a simple calculation. My tests were not as strong as I believed they were, as planting bugs revealed, and replaying runs revealed a date mismatch, as well as contact emails (plus my own user path) that were sitting in every saved snapshot until the replay's privacy scan brought them to light. I don't believe anything to the extent that I treat working once as proof of anything.

The most memorable event for me was the below level 'I'. All the tests were successful when the mode was incorrectly answering the question, since my tests were incorrect as well. This gave me to see that tests were only to verify my own comprehension and not reality. This error was discovered while reading a source about the rule, but not even the Federal Register, due to the blocking of that. I now believe that I (the human) should be in charge of checking with primary sources, and I'm not sure I'm entirely at ease that a secondary summary was my last check.

I also had to answer my own call. The reason I held the push was really my judgement, but when I confirmed the SOC map, I was just approving the AI's draft as the results seemed to be pretty decent. I now know that a gate doesn't really mean much if I don't look at something before I go through it. The employers' actual SOC codes are the ones I'm most concerned with because if I'm mistaken about one, the real outcome could be completely different from what the report says, and nobody reading the report would be able to tell. In the future, I want to check with more questions, ask what is ready to look at, and display my own judgments.

---

## 2026-10-19 — Starting point and choosing the angle

- **[ME]** Shared the assignment brief and chose the folder `TheReallocationEngine_Mode_Build_Assignment/`.
- **[AI]** Read my Assignment 1 work (network-targets recipe, PR #44, SUBMISSION.md) and the repo's
  governing files. It found that the repo already contains the summer copy of this same assignment,
  and that `upstream/main` had not moved since my PR #44 merge base (`015843d`).
- **[AI]** Ran web searches on the current H-1B rules. The wage-weighted selection rule was found to be
  in force since 2026-02-27; DOL's March 2026 prevailing-wage proposal was found to be not final.
- **[AI]** Proposed the lottery-weight angle, keeping my domain (F-1 MSIS, Data Analyst / Data Engineer)
  and persona (Jack Spencer, fictional).
- **Expected:** reuse the engine's metro wage script for local wages.
- **Learned [ME]:** I thought I'd be able to use the engine's metro wage script as it was already in the repo and seemed to be ready to go, but it was based on data from someone else's unmerged PR, so it wasn't actually ready to run on `main`. I thought that if it was in the repo it must have been usable, and that it is for that reason I learned about it before building on it. Also, I saw the impact of the starting context: ensuring that the `upstream/main` did not move, and identifying which H-1B rules were final versus only proposed dictated the angle prior to any code was written. On the next time I inherit a script, I will back-track to where it gets its inputs from and execute it first so I can plan around what it does.

## 2026-10-19 — Fresh clone and engine baseline

- **[AI]** Cloned fresh into the assignment folder with `core.autocrlf=false`, the fix I found in
  Assignment 1. This time `npm run verify` and `npm run doctor` passed on the first try.
- **[AI]** `npm run ats:liveness` on 3 real postings plus 1 made-up job ID: 3 active, the made-up one expired.
- **Happened:** `npm run bls:local-wage` exited 2 with two separate blockers. It only looks for a
  POSIX `.venv/bin/python`, and its data folder `data/bls/local-wage/` is not on `main` at all
  (it came with someone else's unmerged PR #43). So the plan changed to the national OEWS file
  that does ship, with the metro data proposed as a TODO.
- **Learned [ME]:** After Assignment #1, I noticed that the clone passed the first time because the `core.autocrlf = false` fix from Assignment 1 was applied from the start, and it was really worth it so that I could record a fix for the environment for later. When I added a fake job ID to the liveness check, I learned that a good check should be able to say “no” as well as “yes” – if the fake ID returned “yes” I would have realized that the tool was broken. The two types of hidden dependency I discovered in the `bls:local-wage` failure were: a script that requires a POSIX environment and data that is only available on another branch. This was a good choice to switch to the national OEWS file, though I now see that as a compromise: national wages are not as accurate, and so the metro data should not be removed from sight as a TODO, but should be preserved.

## 2026-10-19 — Measuring the data before building

- **[AI]** Measured the 80 Days CSV: 30,369 rows, 1,557 with H-1B fields. `median_salary_offered`
  is company-wide, not per title.
- **[AI]** Searched the O*NET alternate titles: "Data Analyst" appears under 7 occupations. On the
  national ladder, $85,000 lands in a different level under each code.
- **[AI]** Probed my 16 confirmed boards. Greenhouse exposes structured pay (`pay_input_ranges`).
  Sigma's postings have none, but say "$140k - $180k annually" in the text. That led to a strict
  text parser that quotes the sentence for a human to check.
- **Learned [ME]:** Data collection prior to design caused more design changes than planning did. I thought the CSV contained the salary for each job, but it contained the salary for each company, and I found that the one job title "Data Analyst" appears under seven occupations with different salaries, so I realized that the lottery weight is not just something the mode computes. However, it relies on a classification decision that a human must make, and so the output is only as reliable as the classification decision; the mode should display the classification decision it assumed. Probing the boards was a learning experience for me, and I learned that real data comes in a variety of shapes, some of which are organized on boards, and others are embedded in text. I liked that the text parser prefixes the source sentence with a quote, since the human mind can then check the number of the source sentence, rather than relying completely on the parser.

## 2026-10-19 — First live runs

- **[AI]** Wrote `lottery_weight.py`, drafted `soc-map.json` with every family unconfirmed, and wrote
  the persona and offer fixtures. A heredoc mangled the regex backslashes in the persona JSON, so the
  files were rewritten with the file tool.
- **Tried [AI]:** first live run. **Happened:** a crash, `UnicodeEncodeError` on the scorer's `✓`,
  because Windows pipes default to cp1252. Fix: force UTF-8 output in `main()`.
- **[AI]** Tried to delete the crashed run's partial files. A safety check blocked the `rm`, so the
  files were moved to `runs/run-0-crash/` and kept as evidence instead.
- **Tried [AI]:** run-1. **Happened:** gate G3 held as designed: every posting and offer
  `MANUAL-CHECK soc-map-not-confirmed`. A wording bug: the summary said "0 entry-eligible" when
  3 were eligible and 0 bracketed. Fixed.
- **Learned [ME]:** What bothered me about the heredoc problem and the cp1252 crash was the fact that, as far as I could tell, they had nothing to do with the logic of the mode, and that was the point I wanted to make, because there were so many real failures that stemmed from the environment, but not the logic of the mode. There was a little bit of frustration when I saw run-1 stop at gate G3, and I wanted results; but afterwards I was pleased that the gate was doing exactly what it was designed to do and not giving me answers on an SOC map that I hadn't verified. The blocked 'rm' also changed my perspective of failed runs; keeping the crash files is much better than removing them as these will allow me to explain what went wrong later. I had to learn that even a summary line can be deceptive, as the "0 entry-eligible" wording snippet did, so I should always read outputs carefully, rather than simply relying on the fact that the run has completed.

## 2026-10-19 — Tests and break attempts

- **[AI]** 31 offline tests passed on the first run.
- **[AI]** Planted 3 bugs (`>` for `>=`, interpolation, reading the ceiling instead of the floor);
  all 3 were caught. The ceiling bug was caught by only one end-to-end test, so a direct unit test
  was added.
- **Learned [ME]:** I watched 31 tests pass in the first run, and was relieved, but then I planted bugs and realized that it did not tell me how good the tests were. There has been only one indirect end-to-end test, and if it changed then a real bug might have gone undetected. I never thought I would test the tests myself, but I think it's a good way to see where coverage is less than its appearance would suggest and a cheap method. Next time, I will add in some bugs before I trust a green test run, and I will have direct unit tests for any logic that just one test covers.

## 2026-10-19 — My decisions at the gate and on the PR

- **[ME]** G3: confirmed all four SOC families as drafted, after seeing run-1 hold.
- **[ME]** PR: a new PR, with PR #44 left open, and nothing pushed until I confirm. Assignment work first.
- **[AI]** After my sign-off, one test failed: it had relied on the shipped `soc-map.json` staying
  unconfirmed. Fix: tests build their own confirmed or unconfirmed copy.

## 2026-10-19 — Replay found what one live run hid

- **Tried [AI]:** replaying run-2's saved snapshot (run-3). **Happened:** refused with
  "fetched 2026-10-20 is -1 days from as_of 2026-10-19". The fetch time is UTC and the run date is
  local, so a late-evening fetch looked like the future. Fix: compare in local time, plus a regression test.
- **Happened:** `pii-scan` found HR contact emails (Roku, Zoox) inside stored posting text. Fix:
  redact emails and phones at fetch time, and apply the same redaction to the 3 earlier snapshots.
  A replay after redaction made identical decisions. Separately, the crash traceback contained my
  Windows user path, which was scrubbed to `<repo>`.
- **Learned [ME]:** I had considered run-2 to be a success, but re-running it revealed two issues I had not been aware of in the first run: a mismatch of UTC/localtime, only appearing in late evening fetches, and company contact emails in the stored postings that I never imagined I would have to check. Seeing replay as a means to find bugs is not a formality, it is now how I see it, and I will not rely on "it worked once" as a formality that the system is correct. The PII finding also made me realise that there is a responsibility to save evidence, too - snapshots and crash files are very useful, but I need to make sure to review what they contain including my own information, such as the Windows user path. I'll pay attention to redacting at the point of capture the next time, rather than cleaning up after the capture.

## 2026-10-19 — Freezing the code and checking claims

- **[AI]** Ran the final live run (run-4) and its replay (run-5): identical decisions. The national
  medians matched the repo's separate compact CSV for 7/7 codes.
- **[AI]** Caught three report claims that went beyond the evidence and corrected them:
  - a scorer note hard-coded to "0.315";
  - "USCIS has not published…", softened to "no published count was found";
  - "entries Under", a punctuation slip.
- **Tried [AI]:** reading the Federal Register rule text to cite it. **Happened:** the site served a
  bot check. A law-firm summary of the rule was read instead.
- **Happened:** that summary showed a below-Level-I wage can still be registered with an alternative
  wage survey, and counts once. The mode had been scoring it as **0 entries / cannot file**, and every
  test passed, because the tests encoded the same wrong reading. Fix: 0 → 1 entry with a flag. Tests,
  reports and all documents were updated, and the final runs re-ran.
- **Learned [ME]:** This was the key learning from the entire build. All the tests passed while the mode was wrongly telling a below-Level-I candidate that the employer couldn't file, because my tests had the same misreading of the rule as the code. Rather than checking correctness against reality, tests only check consistency with my understanding, and the error was only caught because a source about the rule was checked. I also notice that comparing the rule to a source is my job, because the tests can't do it for me. I'm not comfortable that a law-firm summary was the last check, so reading the Federal Register text itself remains to be done before anyone relies on this. The “no published count was found” lesson I learned on a smaller scale from the softened claims: If you don't have an evidence to support a claim, don't make one.

## 2026-10-19 — Documents, review and G4

- **[AI]** Drafted the recipe, card, domain justification, worked run, run log, sources, talk track,
  cover sheet and zip.
- **[ME]** Read `WORKED-RUN.md` and judged it good. Asked to sign G4 and to hold the commit, push and PR.
- **[AI]** Before recording my G4 sign-off, fetched both Sigma postings again. The quoted pay sentence
  was present in both, word for word. Recorded the signature in the run-4 report with a note that it
  was added after the run.

## 2026-10-21 — This log

- **[ME]** Asked about FRICTIONAL.md, since the assignment brief doesn't list it but my earlier
  assignments had one.
- **[AI]** Assembled this file from the session record, leaving the reflections and "Learned" lines
  for me.
- **[ME]** Wrote "My reflections" and every "Learned" line.

## Open questions [ME + AI]

- What would the OFLC 2026–27 table show for Sigma's New York worksite? The national ladder says
  Level III–IV; it may be lower.
- Do Klaviyo and Sigma actually file these titles under the codes in `soc-map.json`? Only LCA data can say.
- When will the FY2028 registration dates be announced? Every run assumes 2027-03-01.
- Commit, push and PR: pending my confirmation.
