#!/usr/bin/env python3
"""BROKEN-mutants.py — break attempts against lottery_weight.py's own test suite.

Each mutant patches ONE function of the real module with a plausible bug, runs the
full offline suite, and must be caught (at least one failure). A mutant that
survives means the tests do not pin that behavior. Run from the repo root:

    python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/fixtures/BROKEN-mutants.py

Exit 0 only if every mutant is killed.
"""

import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import lottery_weight as L  # noqa: E402
import test_lottery_weight as T  # noqa: E402

REAL_BRACKET, REAL_READ = L.bracket, L.lottery_read


def strict_edge_bracket(wage, pts, thresholds):
    """BUG: '>' instead of '>=' — a wage exactly at a percentile point no longer reaches it."""
    q_lo, q_hi = 0, 100
    for p, v in pts:
        if wage > v:
            q_lo = p
        else:
            q_hi = p
            break
    lmin = sum(1 for t in thresholds if t <= q_lo)
    lmax = sum(1 for t in thresholds if t < q_hi)
    return {"pct_interval": [q_lo, q_hi], "level_min": lmin, "level_max": lmax,
            "entries_min": L.ENTRIES[lmin], "entries_max": L.ENTRIES[lmax]}


def interpolating_bracket(wage, pts, thresholds):
    """BUG: linear interpolation between percentile points -> a single 'confident' level."""
    q = 0.0
    for (p0, v0), (p1, v1) in zip(pts, pts[1:]):
        if v0 <= wage < v1:
            q = p0 + (p1 - p0) * (wage - v0) / (v1 - v0)
    if wage >= pts[-1][1]:
        q = 95.0
    lvl = sum(1 for t in thresholds if t <= q)
    return {"pct_interval": [q, q], "level_min": lvl, "level_max": lvl,
            "entries_min": L.ENTRIES[lvl], "entries_max": L.ENTRIES[lvl]}


def ceiling_read(per_soc, rule="current"):
    """BUG: judges the posted CEILING instead of the floor (the optimistic read)."""
    swapped = []
    for s in per_soc:
        if s["status"] == "ok":
            s = {**s, "rules": {k: {"floor": v["ceiling"], "ceiling": v["ceiling"]} for k, v in s["rules"].items()}}
        swapped.append(s)
    return REAL_READ(swapped, rule)


MUTANTS = [
    ("strict-edge (> not >=)", "bracket", strict_edge_bracket),
    ("interpolate a point estimate", "bracket", interpolating_bracket),
    ("read the ceiling, not the floor", "lottery_read", ceiling_read),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    killed = 0
    for name, attr, fn in MUTANTS:
        original = getattr(L, attr)
        setattr(L, attr, fn)
        try:
            suite = unittest.defaultTestLoader.loadTestsFromModule(T)
            res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        finally:
            setattr(L, attr, original)
        bad = len(res.failures) + len(res.errors)
        names = sorted({t.id().split(".")[-1] for t, _ in res.failures + res.errors})
        status = "KILLED" if bad else "SURVIVED"
        killed += bool(bad)
        print(f"{status:9} {name:34} {bad} failing test(s): {', '.join(names[:4])}{' …' if len(names) > 4 else ''}")
    print(f"{killed}/{len(MUTANTS)} mutants killed")
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
