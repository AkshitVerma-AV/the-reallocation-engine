#!/usr/bin/env python3
"""network_targets.py — pre-OPT Data Analyst / Data Engineer "network, don't apply" list.

Recipe: recipes/cases/2026fa/AkshitVerma-AV-preopt-data-network-targets.md

Pipeline (each step labels every value record / model-judgment / your-input):
  G0  persona dates -> timeline factor            (your-input; exit 3 on failure, nothing written)
      80 Days CSV -> candidates                    (record; phone/executive columns dropped)
      Form D samples + CSV date -> funding evidence (record; missing = "none-in-shipped-data")
  G1  boards.json (your-input, "confirmed": true) -> which boards may be checked
  G2  ATS board API (--live) or a saved snapshot -> live / none / unresolved
      roles.json -> scripts/score/role-scorer.mjs  (the existing scorer, called, not copied)
      scorer output -> APPLY-TAILOR / NETWORK / MANUAL-CHECK / SKIP
  G3  human reads network-targets.md (this script sends nothing)

Standard library only. Network hosts (only with --live): boards-api.greenhouse.io,
api.lever.co, api.ashbyhq.com.

Exit codes: 0 ok · 2 usage/input error · 3 G0 timeline failed · 4 zero candidates ·
5 snapshot too old · 6 scorer failed.
"""

import argparse
import ast
import csv
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CSV_PATH = os.path.join(REPO, "data", "80-days-to-stay", "80-days-csv", "mapped_student_employment_targets_v3.csv")
FORM_D_GLOB = os.path.join(REPO, "data", "sec", "form-d", "processed", "sample", "*.sample.json")
BLS_PATH = os.path.join(REPO, "data", "bls", "compact", "soc_occupation_compact.csv")
SCORER = os.path.join(REPO, "scripts", "score", "role-scorer.mjs")

RECIPE = "preopt-data-network-targets"
RECIPE_VERSION = "0.1.1"
REC, MODEL, INPUT = "record", "model-judgment", "your-input"

# Columns copied out of the CSV. phone, executive_officers and board_directors are
# deliberately NOT here (DATA_CONTRACT §Zero-Conditions; pii-scan only waives data/).
KEEP_COLS = ["company_name", "state", "website", "Total Approvals", "Total Denials",
             "Approval_Rate", "median_salary_offered", "latest_funding_date", "latest_funding_stage"]

# Sponsorship tier rule — your-input, [VERIFY]: Ch.7 says the repo's own thresholds are unreconciled.
TIER_RULE = {"version": "tier-rule v0.1.0",
             "Proven": "approvals >= 50 and approval_rate >= 90 -> p 0.90",
             "Likely": "approvals >= 10 -> p 0.60",
             "Possible": "approvals 1-9 -> p 0.40",
             "None": "approvals == 0 -> p 0.00"}
NETWORK_TIERS = ("Proven", "Likely")
SNAPSHOT_MAX_AGE_DAYS = 7
HTTP_TIMEOUT = 15
USER_AGENT = "reallocation-engine-contrib/preopt-data-network-targets"  # Ashby returns 403 without one

ATS_ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}


class Stop(Exception):
    """A gate or input failure: message for the human, exit code for the agent."""
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def lab(value, source, **extra):
    """Every value leaves this script wearing its source label."""
    return {"value": value, "source": source, **extra}


def parse_date(s):
    return dt.date.fromisoformat(s)


def add_months(d, months):
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(year, month, day)
        except ValueError:
            continue


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# ── G0: timeline ────────────────────────────────────────────────────────────
def timeline_gate(persona, as_of):
    try:
        start = parse_date(persona["opt_start_date"])
        end = parse_date(persona["opt_end_date"])
        ceiling = int(persona["unemployment_ceiling_days"])
        lag = int(persona["hiring_lag_days"])
    except (KeyError, ValueError, TypeError) as e:
        raise Stop(3, f"G0 failed: persona date/number field missing or unparseable ({e})")
    if end <= as_of:
        raise Stop(3, f"G0 failed: opt_end_date {end} is not after as_of {as_of} — OPT window already closed")
    if start > end:
        raise Stop(3, f"G0 failed: opt_start_date {start} is after opt_end_date {end}")
    deadline = start + dt.timedelta(days=ceiling)
    earliest_start = max(as_of + dt.timedelta(days=lag), start)
    slack = (deadline - earliest_start).days
    factor = 0.0 if slack <= 0 else min(1.0, slack / ceiling)
    if factor <= 0.05:
        raise Stop(3, f"G0 failed: timeline factor {factor:.3f} (slack {slack} days to the {deadline} unemployment deadline)")
    return {"factor": round(factor, 4), "source": INPUT, "slack_days": slack,
            "deadline": deadline.isoformat(), "earliest_start": earliest_start.isoformat(),
            "assumptions": {"hiring_lag_days": lab(lag, INPUT), "unemployment_ceiling_days": lab(ceiling, INPUT),
                            "opt_start_date": lab(start.isoformat(), INPUT), "opt_end_date": lab(end.isoformat(), INPUT)},
            "formula": "factor = min(1, (opt_start + ceiling − max(as_of + lag, opt_start)) / ceiling)"}


# ── candidates (record) ─────────────────────────────────────────────────────
def tier_of(approvals, rate):
    if approvals >= 50 and rate >= 90:
        return "Proven", 0.90
    if approvals >= 10:
        return "Likely", 0.60
    if approvals >= 1:
        return "Possible", 0.40
    return "None", 0.00


def load_candidates(title_res, excl_title_res):
    out = []
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if not row["Total Approvals"]:
                continue  # no sponsorship record -> unknown; never p = 0, never a candidate
            try:
                titles = ast.literal_eval(row["top_job_titles_sponsored"] or "[]")
            except (ValueError, SyntaxError):
                titles = []
            matched = [t for t in titles if any(r.search(t) for r in title_res)]
            if not matched:
                continue
            kept = {k: row[k] for k in KEEP_COLS}
            approvals = float(kept["Total Approvals"])
            rate = float(kept["Approval_Rate"] or 0)
            tier, p = tier_of(approvals, rate)
            out.append({"row": kept, "matched_titles": matched, "approvals": approvals,
                        "rate": rate, "tier": tier, "p": p,
                        # flag only (v0.1.1): every matched sponsored data title is senior/non-entry
                        "senior_only_evidence": all(any(r.search(t) for r in excl_title_res) for t in matched)})
    return out


# ── funding evidence (record; requirement for NETWORK) ──────────────────────
def load_form_d():
    idx, files = {}, []
    for path in sorted(glob.glob(FORM_D_GLOB)):
        files.append(os.path.relpath(path, REPO).replace(os.sep, "/"))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for c in data.get("companies", []):
            filed = c.get("filing", {}).get("date_filed")
            try:
                filed_iso = dt.datetime.strptime(filed, "%d-%b-%Y").date().isoformat()
            except (TypeError, ValueError):
                filed_iso = None
            idx.setdefault(norm_name(c["company"]["name"]), []).append({
                "quarter": c.get("filing", {}).get("quarter"), "date_filed": filed_iso,
                "total_amount_sold": c.get("funding", {}).get("total_amount_sold")})
    return idx, files


def funding_evidence(cand, form_d_idx, as_of, window_months):
    cutoff = add_months(as_of, -window_months)
    hits = form_d_idx.get(norm_name(cand["row"]["company_name"]), [])
    dates = [d for d in [cand["row"]["latest_funding_date"]] + [h["date_filed"] for h in hits] if d]
    if not dates:
        status = "none-in-shipped-data"
    elif any(parse_date(d) >= cutoff for d in dates):
        status = "recent"
    else:
        status = "stale"
    return {"latest_funding_date": lab(cand["row"]["latest_funding_date"] or None, REC),
            "latest_funding_stage": lab(cand["row"]["latest_funding_stage"] or None, REC),
            "form_d": hits if hits else "not-in-sample",
            "funding_evidence": lab(status, REC, window_months=lab(window_months, INPUT), cutoff=cutoff.isoformat())}


# ── G1 / G2: boards ─────────────────────────────────────────────────────────
def fetch_board(ats, slug):
    url = ATS_ENDPOINTS[ats].format(slug=slug)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            body = json.load(r)
            status = r.status
    except urllib.error.HTTPError as e:
        return {"url": url, "http_status": e.code, "error": f"HTTP {e.code}", "postings": []}
    except Exception as e:  # network error, timeout, bad JSON
        return {"url": url, "http_status": None, "error": f"{type(e).__name__}: {e}", "postings": []}
    if ats == "greenhouse":
        raw = [(j.get("title"), (j.get("location") or {}).get("name"), j.get("absolute_url")) for j in body.get("jobs", [])]
    elif ats == "lever":
        raw = [(j.get("text"), (j.get("categories") or {}).get("location"), j.get("hostedUrl")) for j in body]
    else:
        raw = [(j.get("title"), j.get("location"), j.get("jobUrl")) for j in body.get("jobs", [])]
    return {"url": url, "http_status": status, "error": None,
            "postings": [{"title": t or "", "location": l or "", "url": u} for t, l, u in raw]}


def classify_board(board, persona, title_res, excl_title_res):
    """live / none / unresolved — unresolved is "I don't know", never "nothing open"."""
    if board.get("http_status") != 200:
        return "unresolved", f"board fetch failed ({board.get('error') or board.get('http_status')})", [], 0
    postings = board.get("postings", [])
    if not postings:
        return "unresolved", "board returned zero postings total (likely moved ATS) — not evidence of no openings", [], 0
    excl_locs = [s.lower() for s in persona.get("exclude_posting_location_patterns", [])]
    prefs = [s.lower() for s in persona.get("preferred_locations", [])]
    matched, excluded_by_title = [], 0
    for p in postings:
        if not any(r.search(p["title"]) for r in title_res):
            continue
        if any(s in p["location"].lower() for s in excl_locs):
            continue
        if any(r.search(p["title"]) for r in excl_title_res):
            excluded_by_title += 1
            continue
        matched.append({**p, "preferred_location": any(s in p["location"].lower() for s in prefs)})
    if matched:
        return "live", f"{len(matched)} entry-eligible US data posting(s) of {len(postings)}", matched, excluded_by_title
    note = f" ({excluded_by_title} senior/intern/contract data posting(s) excluded)" if excluded_by_title else ""
    return "none", f"0 entry-eligible US data postings of {len(postings)}{note}", [], excluded_by_title


# ── wage context (record; NOT a scorer input — role_quality weight is 0.0) ──
def wage_context(target_soc):
    rows = {}
    with open(BLS_PATH, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows[r["onet_soc_code"]] = r
    out = []
    for code in target_soc:
        r = rows.get(code)
        if r is None:
            out.append({"onet_soc_code": code, "status": "missing", "reason": "no row in soc_occupation_compact.csv"})
        else:
            out.append({"onet_soc_code": code, "status": "ok", "title": r["title"], "bls_soc_code": r["bls_soc_code"],
                        "annual_median_wage": lab(float(r["annual_median_wage"]) if r["annual_median_wage"] else None, REC),
                        "oews_year": r["oews_year"],
                        "note": "national OEWS median for the parent BLS code, not Chicago, not this O*NET detail"})
    return out


# ── output-dir guard: never write over a tracked repo file ──────────────────
ALLOWED_IN_REPO = ("course/2026fa/submissions/AkshitVerma-AV/", "scripts/contrib/2026fa/AkshitVerma-AV-")


def check_out_dir(out_dir):
    rel = os.path.relpath(os.path.abspath(out_dir), REPO).replace(os.sep, "/") + "/"
    if not rel.startswith("../") and not rel.startswith(ALLOWED_IN_REPO):
        raise Stop(2, f"--out-dir {out_dir} is inside the repo but outside this contribution's namespaces {ALLOWED_IN_REPO}")


def run(args):
    as_of = parse_date(args.as_of) if args.as_of else dt.date.today()
    with open(args.persona, encoding="utf-8") as f:
        persona = json.load(f)
    check_out_dir(args.out_dir)

    timeline = timeline_gate(persona, as_of)  # G0 — raises before anything is written

    title_res = [re.compile(p, re.I) for p in persona["target_title_patterns"]]
    excl_title_res = [re.compile(p, re.I) for p in persona.get("exclude_posting_title_patterns", [])]
    cands = load_candidates(title_res, excl_title_res)
    if not cands:
        raise Stop(4, "zero candidates after the title filter — the patterns or the CSV changed")

    with open(args.boards, encoding="utf-8") as f:
        board_map = {b["company_name"]: b for b in json.load(f)["boards"]}

    snapshot = None
    if not args.live:
        if not args.snapshot:
            raise Stop(2, "pass --live (network) or --snapshot <board-snapshot.json> (offline)")
        with open(args.snapshot, encoding="utf-8") as f:
            snapshot = json.load(f)
        fetched = dt.datetime.fromisoformat(snapshot["fetched_at"]).date()
        age = (as_of - fetched).days
        if age > SNAPSHOT_MAX_AGE_DAYS:
            raise Stop(5, f"G2 failed: snapshot fetched {fetched} is {age} days before as_of {as_of} (max {SNAPSHOT_MAX_AGE_DAYS})")

    form_d_idx, form_d_files = load_form_d()
    os.makedirs(args.out_dir, exist_ok=True)

    cand_names = {c["row"]["company_name"] for c in cands}
    board_map_unmatched = [{"company_name": n, "reason": "not a candidate (absent from CSV, no sponsorship record, or no data title) — never scored"}
                           for n in board_map if n not in cand_names]

    # G1 + G2
    companies, snap_out = [], {"fetched_at": None, "mode": "live" if args.live else "snapshot", "boards": {}}
    if args.live:
        snap_out["fetched_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    else:
        snap_out["fetched_at"] = snapshot["fetched_at"]
        snap_out["replayed_from"] = os.path.relpath(os.path.abspath(args.snapshot), REPO).replace(os.sep, "/")
    for c in cands:
        name = c["row"]["company_name"]
        entry = {"cand": c, "funding": funding_evidence(c, form_d_idx, as_of, int(persona["funding_window_months"]))}
        b = board_map.get(name)
        if b is None:
            entry.update(board_status="unresolved", board_reason="no-board-in-map (G1)", board=None)
        elif b.get("confirmed") is not True:
            entry.update(board_status="unresolved", board_reason="board-not-confirmed (G1: a human must set \"confirmed\": true)", board=b)
        elif b.get("ats") not in ATS_ENDPOINTS:
            entry.update(board_status="unresolved", board_reason=f"unsupported ATS {b.get('ats')!r}", board=b)
        else:
            if args.live:
                raw = fetch_board(b["ats"], b["slug"])
                snap_out["boards"][name] = {"ats": b["ats"], "slug": b["slug"], **raw}
            else:
                raw = snapshot["boards"].get(name)
                if raw is None:
                    raw = {"http_status": None, "error": "company not in snapshot", "postings": []}
                snap_out["boards"][name] = raw
            status, reason, matched, excluded = classify_board(raw, persona, title_res, excl_title_res)
            entry.update(board_status=status, board_reason=reason, board=b,
                         board_detail={"http_status": raw.get("http_status"), "url": raw.get("url"),
                                       "postings_total": len(raw.get("postings", [])),
                                       "postings_matched": matched, "excluded_by_title_rule": excluded})
        companies.append(entry)

    write_json(os.path.join(args.out_dir, "candidates.json"), {
        "as_of": as_of.isoformat(), "source_csv": os.path.relpath(CSV_PATH, REPO).replace(os.sep, "/"),
        "columns_kept": KEEP_COLS, "columns_dropped": "every other CSV column, including phone, executive_officers, board_directors",
        "candidates": [{"company_name": lab(e["cand"]["row"]["company_name"], REC), "match_method": "exact company_name in boards.json",
                        "website": lab(e["cand"]["row"]["website"] or None, REC, note="may be generated from the name; not identity evidence"),
                        "matched_titles": lab(e["cand"]["matched_titles"], REC),
                        "g1": "confirmed" if (e["board"] or {}).get("confirmed") is True else e["board_reason"]}
                       for e in companies]})
    write_json(os.path.join(args.out_dir, "board-snapshot.json"), snap_out)

    # Score: only live/none go to the scorer. A missing liveness defaults to 1.0 in role-scorer.mjs,
    # so an unresolved company must never be sent.
    roles = []
    for i, e in enumerate(companies):
        if e["board_status"] not in ("live", "none"):
            continue
        c = e["cand"]
        e["role_id"] = f"c{i:03d}-{norm_name(c['row']['company_name'])[:24]}"
        roles.append({
            "role_id": e["role_id"], "company": c["row"]["company_name"], "title": "Data Analyst / Data Engineer (company-level)",
            "sponsorship": {"p": c["p"], "tier": c["tier"], "source": REC,
                            "basis": {"approvals": c["approvals"], "approval_rate": c["rate"], "rule": TIER_RULE["version"], "rule_source": INPUT}},
            "liveness": {"factor": 1.0 if e["board_status"] == "live" else 0.0, "source": REC, "basis": e["board_reason"]},
            "timeline": {"factor": timeline["factor"], "source": INPUT, "basis": timeline["formula"]},
        })
    roles_path = os.path.join(args.out_dir, "roles.json")
    write_json(roles_path, roles)
    scored = {}
    if not roles:
        print("! no company reached the scorer (no confirmed board returned live/none) — everything is MANUAL-CHECK", file=sys.stderr)
    if roles:
        proc = subprocess.run(["node", SCORER, roles_path, "--out-dir", args.out_dir], capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            raise Stop(6, f"scorer failed (exit {proc.returncode}): {proc.stderr.strip()}")
        print(proc.stdout.strip())
        with open(os.path.join(args.out_dir, "role-scores.json"), encoding="utf-8") as f:
            scored = {r["role_id"]: r for r in json.load(f)["roles"]}

    # Bucket from the scorer's own output
    for e in companies:
        c, fund = e["cand"], e["funding"]["funding_evidence"]["value"]
        s = scored.get(e.get("role_id"))
        e["scorer"] = None
        if s is None:
            e["bucket"], e["bucket_reason"] = "MANUAL-CHECK", e["board_reason"]
            e["next_action"] = "10 min on the careers page: find the real ATS, fix boards.json, or strike the company"
            continue
        e["scorer"] = {"recommendation": s["recommendation"], "machine_recommendation": s["machine_recommendation"],
                       "reason": s["reason"], "composite": s["composite"], "arithmetic": s["trace"]["arithmetic"], "source": "role-scores.json"}
        gated_by_liveness = s["machine_recommendation"] == "Skip" and s["reason"].startswith("gated: liveness")
        if s["recommendation"] in ("Apply", "Consider"):
            e["bucket"], e["bucket_reason"] = "APPLY-TAILOR", f"scorer {s['recommendation']}: {s['reason']}"
            e["next_action"] = "open the matched posting(s), judge fit by hand, tailor one application (the 2)"
        elif gated_by_liveness and c["tier"] in NETWORK_TIERS and fund == "recent":
            e["bucket"], e["bucket_reason"] = "NETWORK", f"no entry-eligible data posting; {c['tier']} sponsor; funding {fund}"
            e["next_action"] = "find one data-team employee or alum for a 20-min informational interview; re-check board in 14 days (the 3)"
        elif gated_by_liveness and c["tier"] in NETWORK_TIERS:
            label = "funding stale" if fund == "stale" else "no funding evidence in shipped data"
            e["bucket"], e["bucket_reason"] = "SKIP", f"network-blocked: {label}"
            e["next_action"] = "none by rule; a human may override after checking funding outside the shipped data"
        else:
            e["bucket"], e["bucket_reason"] = "SKIP", f"scorer {s['machine_recommendation']}: {s['reason']}"
            e["next_action"] = "none — time goes back to the day"

    result = build_result(args, as_of, persona, timeline, companies, board_map_unmatched, form_d_files)
    write_json(os.path.join(args.out_dir, "network-targets.json"), result)
    with open(os.path.join(args.out_dir, "network-targets.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(result))
    counts = result["counts"]
    print(f"✓ {counts['candidates']} candidates → APPLY-TAILOR {counts['APPLY-TAILOR']} · NETWORK {counts['NETWORK']} · "
          f"MANUAL-CHECK {counts['MANUAL-CHECK']} · SKIP {counts['SKIP']} (network-blocked {counts['network_blocked']})")
    print(f"  {os.path.relpath(os.path.join(args.out_dir, 'network-targets.json'))}  +  network-targets.md")
    return result


def build_result(args, as_of, persona, timeline, companies, board_map_unmatched, form_d_files):
    rows = []
    for e in companies:
        c = e["cand"]
        b = e.get("board") or {}
        rows.append({
            "company": lab(c["row"]["company_name"], REC),
            "state": lab(c["row"]["state"], REC),
            "website": lab(c["row"]["website"] or None, REC),
            "bucket": e["bucket"], "bucket_reason": e["bucket_reason"],
            "sponsorship": {"approvals": lab(c["approvals"], REC), "denials": lab(float(c["row"]["Total Denials"] or 0), REC),
                            "approval_rate": lab(round(c["rate"], 2), REC),
                            "tier": lab(c["tier"], INPUT, basis=TIER_RULE["version"], p=c["p"]),
                            "matched_titles": lab(c["matched_titles"], REC),
                            "senior_only_evidence": lab(c["senior_only_evidence"], REC,
                                                        note="flag only: every matched sponsored data title hits the persona's excluded-title patterns [your-input]; changes no bucket"),
                            "median_salary_offered_all_titles": lab(float(c["row"]["median_salary_offered"]) if c["row"]["median_salary_offered"] else None, REC)},
            "board": {"status": e["board_status"], "reason": e["board_reason"],
                      "ats": lab(b.get("ats"), INPUT) if b else None, "slug": lab(b.get("slug"), INPUT) if b else None,
                      "confirmed": lab(b.get("confirmed"), INPUT) if b else None,
                      **({k: v for k, v in e.get("board_detail", {}).items()}),
                      "source": REC if e.get("board_detail") else None},
            "funding": e["funding"],
            "scorer": e["scorer"],
            "next_action": e["next_action"],
        })
    order = {"NETWORK": 0, "APPLY-TAILOR": 1, "MANUAL-CHECK": 2, "SKIP": 3}
    rows.sort(key=lambda r: (order[r["bucket"]], -r["sponsorship"]["approvals"]["value"]))
    count = lambda b: sum(r["bucket"] == b for r in rows)
    pl = [r for r in rows if r["sponsorship"]["tier"]["value"] in NETWORK_TIERS]
    return {
        "recipe": RECIPE, "recipe_version": RECIPE_VERSION, "as_of": as_of.isoformat(),
        "persona": {"file": os.path.relpath(os.path.abspath(args.persona), REPO).replace(os.sep, "/"), "name": lab(persona.get("name"), INPUT),
                    "fictional": True, "target_soc": lab(persona["target_soc"], INPUT)},
        "data_used": {"csv": os.path.relpath(CSV_PATH, REPO).replace(os.sep, "/"), "form_d": form_d_files,
                      "form_d_note": "samples only (50 companies per quarter); absence = not-in-sample, not unfunded",
                      "bls": os.path.relpath(BLS_PATH, REPO).replace(os.sep, "/"),
                      "board_mode": "live" if args.live else "snapshot",
                      "scorer": "scripts/score/role-scorer.mjs (called, not copied)"},
        "timeline": timeline,
        "tier_rule": lab(TIER_RULE, INPUT, note="[VERIFY] thresholds are not pinned by the repo (Ch.7)"),
        "counts": {"candidates": len(rows), "APPLY-TAILOR": count("APPLY-TAILOR"), "NETWORK": count("NETWORK"),
                   "MANUAL-CHECK": count("MANUAL-CHECK"), "SKIP": count("SKIP"),
                   "network_blocked": sum(r["bucket_reason"].startswith("network-blocked") for r in rows),
                   "proven_or_likely": len(pl),
                   "proven_or_likely_with_recent_funding": sum(r["funding"]["funding_evidence"]["value"] == "recent" for r in pl)},
        "wage_context": wage_context(persona["target_soc"]),
        "board_map_unmatched": board_map_unmatched,
        "companies": rows,
        "cannot_verify": CANNOT_VERIFY,
        "g3": {"signed_by": None, "note": "a human chooses whom to contact; this script sent nothing"},
    }


CANNOT_VERIFY = [
    "That the company sponsors data roles specifically: approvals are company-wide; a data title in the top-N list is the only role signal; the DOL year window is undocumented.",
    "That the company sponsors new grads, or sponsors today: the record is backward-looking.",
    "That the CSV company and the ATS board are the same entity: a human confirmed each mapping at G1.",
    "That 'none' means 'not hiring': roles may be on another ATS, with recruiters, or open next week.",
    "That a 'live' posting is not a ghost posting: listed is not the same as hiring.",
    "That a company without funding evidence is unfunded: Form D ships as 4×50-company samples; CSV funding dates are mostly years old.",
    "Location eligibility beyond the excluded-location list; Chicago pay (wage shown is national, parent BLS code); fit (not scored).",
]


def fmt_money(x):
    return "—" if x is None else f"${x:,.0f}"


def render_md(r):
    c = r["counts"]
    o = [f"# Network targets — {r['persona']['name']['value']} (fictional) — {r['as_of']}", "",
         "## Executive summary", "",
         f"{c['candidates']} companies in the 80 Days CSV have an H-1B record **and** a data title among their top sponsored titles [record]. "
         f"Result: **NETWORK {c['NETWORK']}** · APPLY-TAILOR {c['APPLY-TAILOR']} · MANUAL-CHECK {c['MANUAL-CHECK']} · SKIP {c['SKIP']}. "
         f"Skip + manual-check share: {(c['SKIP'] + c['MANUAL-CHECK']) / c['candidates'] * 100:.0f}%.", "",
         f"Funding is a NETWORK requirement [your-input]: of {c['proven_or_likely']} Proven/Likely sponsors, only "
         f"{c['proven_or_likely_with_recent_funding']} have funding evidence within {r['companies'][0]['funding']['funding_evidence']['window_months']['value']} months in the shipped data. "
         f"**{c['network_blocked']} scored sponsors were blocked from NETWORK by missing or stale funding data only** — listed below, not hidden.", "",
         f"Timeline gate [your-input]: factor {r['timeline']['factor']} — earliest start {r['timeline']['earliest_start']}, "
         f"90-day unemployment deadline {r['timeline']['deadline']}, slack {r['timeline']['slack_days']} days "
         f"(hiring lag {r['timeline']['assumptions']['hiring_lag_days']['value']} days is an assumption).", "",
         f"Data used: `{r['data_used']['csv']}`; Form D samples {len(r['data_used']['form_d'])} files; board mode **{r['data_used']['board_mode']}**; "
         f"decision by `{r['data_used']['scorer']}`. Labels: [record] from a file or API response, [your-input] chosen by the person, [model-judgment] none in this report.", ""]

    def tbl(title, rows, cols, blurb=None):
        o.append(f"## {title} ({len(rows)})")
        o.append("")
        if blurb:
            o.extend([blurb, ""])
        if not rows:
            o.extend(["*(none)*", ""])
            return
        o.append("| " + " | ".join(h for h, _ in cols) + " |")
        o.append("|" + "---|" * len(cols))
        for row in rows:
            o.append("| " + " | ".join(str(f(row)).replace("|", "/") for _, f in cols) + " |")
        o.append("")

    rows = r["companies"]
    sp = lambda x: (f"{x['sponsorship']['tier']['value']} [your-input rule] · {x['sponsorship']['approvals']['value']:.0f} appr / {x['sponsorship']['approval_rate']['value']}% [record]"
                    + (" · ⚠ senior-only data-title evidence" if x["sponsorship"]["senior_only_evidence"]["value"] else ""))
    fund = lambda x: f"{x['funding']['funding_evidence']['value']} (CSV {x['funding']['latest_funding_date']['value'] or '—'}; Form D {'hit' if x['funding']['form_d'] != 'not-in-sample' else 'not-in-sample'}) [record]"
    board = lambda x: f"{x['board']['status']}: {x['board']['reason']} [record]"
    titles = lambda x: "; ".join(x["sponsorship"]["matched_titles"]["value"][:3]) + " [record]"
    comp = lambda x: f"{x['scorer']['composite']} ({x['scorer']['arithmetic']})" if x["scorer"] else "not scored"

    tbl("NETWORK — network, don't apply", [x for x in rows if x["bucket"] == "NETWORK"],
        [("Company", lambda x: f"{x['company']['value']} ({x['state']['value']})"), ("Sponsorship", sp), ("Sponsored data titles", titles),
         ("Board", board), ("Funding", fund), ("Scorer", comp), ("Next action", lambda x: x["next_action"])],
        "Scorer skipped these **only** because the liveness gate is closed; strong sponsor; recent funding. Spend networking hours here.")
    tbl("APPLY-TAILOR", [x for x in rows if x["bucket"] == "APPLY-TAILOR"],
        [("Company", lambda x: x["company"]["value"]), ("Sponsorship", sp), ("Scorer", lambda x: f"{x['scorer']['recommendation']} — {comp(x)}"),
         ("Matched postings [record]", lambda x: "<br>".join(f"{p['title']} — {p['location']}{' ★' if p['preferred_location'] else ''} {p['url']}" for p in x["board"].get("postings_matched", [])[:4]))],
        "Fit is **not** scored (no fit term was sent). Composite comes from sponsorship × gates only — read each posting before tailoring. ★ = preferred location [your-input].")
    tbl("SKIP — network-blocked by funding data", [x for x in rows if x["bucket_reason"].startswith("network-blocked")],
        [("Company", lambda x: x["company"]["value"]), ("Sponsorship", sp), ("Board", board), ("Funding", fund), ("Why", lambda x: x["bucket_reason"])],
        "Would be NETWORK targets except for the funding requirement. Absence of funding evidence is a data gap (Fact 3), not evidence against the company.")
    mc = [x for x in rows if x["bucket"] == "MANUAL-CHECK"]
    mc_pl = [x for x in mc if x["sponsorship"]["tier"]["value"] in NETWORK_TIERS]
    tbl("MANUAL-CHECK — Proven/Likely first", mc_pl,
        [("Company", lambda x: f"{x['company']['value']} ({x['state']['value']})"), ("Sponsorship", sp), ("Website", lambda x: x["website"]["value"] or "—"),
         ("Why", lambda x: x["bucket_reason"]), ("Funding", fund)],
        "`unresolved` means *unknown*, not *nothing open*. These never reached the scorer.")
    rest = [x["company"]["value"] for x in mc if x not in mc_pl]
    if rest:
        o.extend([f"Possible-tier MANUAL-CHECK ({len(rest)}, low priority): " + ", ".join(rest), ""])
    other = [x for x in rows if x["bucket"] == "SKIP" and not x["bucket_reason"].startswith("network-blocked")]
    tbl("SKIP — other", other, [("Company", lambda x: x["company"]["value"]), ("Sponsorship", sp), ("Why", lambda x: x["bucket_reason"])])

    o.extend(["## Wage context (not a scorer input)", "",
              "role_quality carries weight 0.0 in the scorer (Fact 1); this is context only.", ""])
    for w in r["wage_context"]:
        if w["status"] == "ok":
            o.append(f"- {w['onet_soc_code']} {w['title']}: national median {fmt_money(w['annual_median_wage']['value'])} [record, OEWS {w['oews_year']}, parent BLS {w['bls_soc_code']}] — not Chicago pay.")
        else:
            o.append(f"- {w['onet_soc_code']}: **missing** — {w['reason']}. No wage invented.")
    if r["board_map_unmatched"]:
        o.extend(["", "## boards.json entries that are not candidates (never scored)", ""])
        o.extend(f"- {u['company_name']}: {u['reason']}" for u in r["board_map_unmatched"])
    o.extend(["", "## What this run cannot verify", ""])
    o.extend(f"- {s}" for s in r["cannot_verify"])
    o.extend(["", "## G3 — human sign-off", "",
              "This report sent nothing to anyone. Chosen for outreach (name, why): ______  Signed: ______  Date: ______", ""])
    return "\n".join(o)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252 and cannot print ✓ / ✗
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--persona", required=True)
    ap.add_argument("--boards", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--live", action="store_true", help="fetch boards from the three named ATS APIs")
    ap.add_argument("--snapshot", help="replay a saved board-snapshot.json (offline)")
    ap.add_argument("--as-of", help="run date YYYY-MM-DD (default: today)")
    args = ap.parse_args(argv)
    try:
        run(args)
    except Stop as s:
        print(f"✗ {s}", file=sys.stderr)
        return s.code
    except (OSError, KeyError, json.JSONDecodeError) as e:
        print(f"✗ input error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
