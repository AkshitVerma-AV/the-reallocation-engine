# run-0-crash — first live attempt, 2026-10-19

## Executive summary

The first live run crashed after the scorer had already run. The Windows console could not print a check-mark character, so the report was never written. These are the partial files it left behind, kept as evidence. The fix (force UTF-8 output) is in the script's `main()`, and run-1 is the same command after the fix.

## Record

- Error: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'` at `print(proc.stdout.strip())` (Python 3.12, stdout piped → cp1252).
- Left behind: `roles.json`, `role-scores.json`, `role-scores.md`. No `lottery-weight.*` was written.
