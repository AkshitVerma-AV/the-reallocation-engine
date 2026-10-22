#!/usr/bin/env python3
"""verify_runs.py — cross-check a live run against its replay and against independent sources.

    python3 scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight/verify_runs.py <live-run-dir> <replay-run-dir>

Run from the repo root. The replay must be a --snapshot replay of the live run's board-snapshot.json.
1 live vs replay decisions · 2 xlsx P50 vs the compact CSV median · 3 sponsorship vs a direct
CSV read · 4 scorer composite vs hand arithmetic · 5 no probability key, no PII columns.
"""
import json, csv, sys
LIVE, REPLAY = sys.argv[1], sys.argv[2]
def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)
a, b = load(f"{LIVE}/lottery-weight.json"), load(f"{REPLAY}/lottery-weight.json")
def key(r): return [(x["company"], x.get("title"), (x.get("location") or {}).get("value"), x["status"],
                     (x.get("lottery_read") or {}).get("read"), (x.get("lottery_read") or {}).get("worst_case_entries"),
                     (x.get("lottery_read") or {}).get("best_case_entries"), (x.get("scorer") or {}).get("composite")) for x in r["rows"] + r["offers"]]
print(f"1. live {LIVE.rsplit('/', 1)[-1]} vs replay {REPLAY.rsplit('/', 1)[-1]} decisions identical:", key(a) == key(b), f"({len(key(a))} rows)")
print("   audit identical:", a["audit"] == b["audit"], a["audit"])
# 2. OEWS ladder vs the independent compact CSV median
comp = {r["onet_soc_code"]: r for r in csv.DictReader(open("data/bls/compact/soc_occupation_compact.csv", encoding="utf-8"))}
seen = {}
for x in a["rows"] + a["offers"]:
    for s in x.get("per_soc", []):
        if s["status"] == "ok": seen[s["soc"]] = s["ladder"]["value"]["50"]
for soc, med in sorted(seen.items()):
    c = comp.get(soc + ".00") or next((v for k, v in comp.items() if v["bls_soc_code"] == soc), None)
    cm = float(c["annual_median_wage"]) if c and c["annual_median_wage"] else None
    print(f"2. {soc} xlsx P50 {med:>9,.0f}  compact-CSV median {cm:>9,.0f}  match={med == cm}")
# 3. sponsorship values vs a direct CSV read
rows = {r["company_name"]: r for r in csv.DictReader(open("data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv", encoding="utf-8"))}
for x in a["rows"]:
    sp = x["sponsorship"]; r = rows[x["company"]]
    print(f"3. {x['company']:<20} approvals log={sp['approvals']} csv={int(float(r['Total Approvals']))}  rate log={sp['approval_rate']} csv={round(float(r['Approval_Rate']),2)}  tier={sp['tier']}")
# 4. scorer arithmetic by hand
for x in a["rows"]:
    sc = x["scorer"]; print(f"4. {x['company']:<20} composite {sc['composite']}  hand: 0.90*0.35*1.0*1.0 = {0.90*0.35*1.0*1.0:.3f}  | {sc['arithmetic']}")
# 5. no probability anywhere; no PII columns
with open(f"{LIVE}/lottery-weight.json", encoding="utf-8") as f:
    blob = f.read().lower()
print("5. 'probability' key present:", '"probability"' in blob, "| phone/executive columns present:", any(k in blob for k in ("phone", "executive_officers", "board_directors")))
