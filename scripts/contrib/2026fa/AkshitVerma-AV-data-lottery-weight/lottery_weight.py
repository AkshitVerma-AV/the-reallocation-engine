#!/usr/bin/env python3
"""lottery_weight.py — how many H-1B lottery entries could this data posting's pay earn?

Recipe: recipes/cases/2026fa/AkshitVerma-AV-data-lottery-weight.md

Since the FY2027 cap season, USCIS selects H-1B registrations by wage level:
Level I = 1 entry, II = 2, III = 3, IV = 4 (DHS weighted-selection rule,
90 FR 60864, effective 2026-02-27). The level depends on the offered wage, the
SOC code the employer files under, and the worksite's prevailing wage. A
student sees only the posted pay range. This script brackets that range
against the national OEWS percentile ladder for every SOC code the employer
could plausibly file, and reports the entry count as a range, never a point.

Pipeline (every value is labeled record / model-judgment / your-input):
  G0  persona dates + registration windows -> lottery attempts   (exit 3 if zero)
  G1  boards.json (human-confirmed)        -> which boards may be fetched
  G2  ATS board API (--live) or snapshot   -> live postings; pay fields; non-live never bracketed
  G3  soc-map.json (human-confirmed)       -> plausible SOC codes per title family
      national OEWS May 2024 (record)      -> percentile bracket -> level range -> entry range
      roles.json -> scripts/score/role-scorer.mjs (called, not copied)
  G4  human reads lottery-weight.md and signs the run log (this script sends nothing)

Standard library only. Network hosts (only with --live): boards-api.greenhouse.io,
api.lever.co, api.ashbyhq.com.

Exit codes: 0 ok · 2 usage/input error · 3 G0 failed (no reachable registration
window) · 4 OEWS file unreadable or fails conformance · 5 snapshot too old ·
6 scorer failed.
"""

import argparse
import ast
import csv
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CSV_PATH = os.path.join(REPO, "data", "80-days-to-stay", "80-days-csv", "mapped_student_employment_targets_v3.csv")
OEWS_PATH = os.path.join(REPO, "data", "bls", "oesm24nat", "national_M2024_dl.xlsx")
SCORER = os.path.join(REPO, "scripts", "score", "role-scorer.mjs")

RECIPE = "data-lottery-weight"
RECIPE_VERSION = "0.1.0"
REC, MODEL, INPUT = "record", "model-judgment", "your-input"

# Columns copied out of the 80 Days CSV. phone, executive_officers and
# board_directors are deliberately NOT here (DATA_CONTRACT §Zero-Conditions).
KEEP_COLS = ["company_name", "state", "Total Approvals", "Total Denials", "Approval_Rate",
             "median_salary_offered", "top_job_titles_sponsored"]

# Same tier rule as AkshitVerma-AV-preopt-data-network-targets v0.1.1 — your-input, [VERIFY]:
# Ch.7 says the repo's own sponsorship thresholds are unreconciled.
TIER_RULE = {"version": "tier-rule v0.1.0",
             "Proven": "approvals >= 50 and approval_rate >= 90 -> p 0.90",
             "Likely": "approvals >= 10 -> p 0.60",
             "Possible": "approvals 1-9 -> p 0.40",
             "None": "approvals == 0 or no row -> p 0.00"}

# The percentile ladder OEWS publishes. Nothing between these points is known,
# so nothing between them is interpolated.
KNOWN_PCTS = [(10, "A_PCT10"), (25, "A_PCT25"), (50, "A_MEDIAN"), (75, "A_PCT75"), (90, "A_PCT90")]
OEWS_REQUIRED = ["AREA_TITLE", "OCC_CODE", "OCC_TITLE", "O_GROUP", "TOT_EMP"] + [c for _, c in KNOWN_PCTS]

# Wage-level thresholds as OEWS percentile equivalents. These are approximations:
# OFLC computes Level I and IV from the OEWS distribution and II/III by the
# statutory formula, so the exact dollar cut-offs come only from the OFLC table
# ([TODO: DATA SOURCE] in the recipe).
RULES = {
    "current": {"thresholds": [17, 34, 50, 67], "status": "in force",
                "basis": "OFLC four-level structure, commonly cited as ~17th/34th/50th/67th OEWS percentiles; "
                         "used by the weighted selection rule (90 FR 60864, effective 2026-02-27)"},
    "dol-nprm-2026": {"thresholds": [34, 52, 70, 88], "status": "PROPOSED, NOT IN FORCE",
                      "basis": "DOL proposed rule published 2026-03-27 (docket ETA-2026-0001); not final as of the recipe date"},
}
# level -> lottery entries. Level 0 = below the Level I proxy: the rule still lets the employer register
# if an acceptable alternative wage source supports the wage, and such registrations are entered once
# (GT Law summary of 90 FR 60864; SOURCES.md). So 0 maps to 1 entry, flagged below_level_I_possible.
ENTRIES = {0: 1, 1: 1, 2: 2, 3: 3, 4: 4}

SNAPSHOT_MAX_AGE_DAYS = 7
HTTP_TIMEOUT = 20
USER_AGENT = "reallocation-engine-contrib/data-lottery-weight"  # Ashby returns 403 without one
LIST_ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
}
GH_DETAIL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{id}?pay_transparency=true"

PAY_MIN, PAY_MAX = 20000, 1000000  # sanity bounds for an annual base salary in USD


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
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(d.year + y, m + 1, day)
        except ValueError:
            continue


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# ── G0: timeline — OPT clock and reachable lottery windows ──────────────────
def timeline_gate(persona, as_of):
    try:
        start = parse_date(persona["opt_start_date"])
        end = parse_date(persona["opt_end_date"])
        ceiling = int(persona["unemployment_ceiling_days"])
        lag = int(persona["hiring_lag_days"])
        stem = bool(persona["stem_opt_eligible"])
        stem_months = int(persona.get("stem_opt_months", 24))
        windows = persona["registration_windows"]
    except (KeyError, ValueError, TypeError) as e:
        raise Stop(3, f"G0 failed: persona timeline field missing or unparseable ({e})")
    if start > end:
        raise Stop(3, f"G0 failed: opt_start_date {start} is after opt_end_date {end}")
    authorized_through = add_months(end, stem_months) if stem else end
    if authorized_through <= as_of:
        raise Stop(3, f"G0 failed: work authorization ends {authorized_through}, not after as_of {as_of}")
    offer_by_earliest = as_of + dt.timedelta(days=lag)
    attempts = []
    for w in windows:
        opens = parse_date(w["opens"])
        reasons = []
        if opens < offer_by_earliest:
            reasons.append(f"opens {opens}, before the earliest offer date {offer_by_earliest} (as_of + {lag}-day hiring lag)")
        if opens > authorized_through:
            reasons.append(f"opens {opens}, after work authorization ends {authorized_through}")
        if not stem and opens > end:
            reasons.append("needs the STEM OPT extension, which this persona does not have")
        attempts.append({"fiscal_year": w["fy"], "opens": lab(opens.isoformat(), INPUT, assumed=bool(w.get("assumed"))),
                         "reachable": not reasons, "why_not": reasons})
    reachable = [a for a in attempts if a["reachable"]]
    if not reachable:
        raise Stop(3, "G0 failed: no H-1B registration window is reachable before work authorization ends — "
                      "the mode refuses to bracket wages for a lottery the persona cannot enter")
    # Scorer timeline factor: same formula as the network-targets recipe (OPT unemployment clock).
    deadline = start + dt.timedelta(days=ceiling)
    earliest_start = max(offer_by_earliest, start)
    slack = (deadline - earliest_start).days
    factor = 0.0 if slack <= 0 else min(1.0, slack / ceiling)
    return {"authorized_through": lab(authorized_through.isoformat(), INPUT,
                                      basis=f"opt_end_date + {stem_months} months STEM OPT" if stem else "opt_end_date (no STEM OPT)"),
            "stem_opt_eligible": lab(stem, INPUT), "attempts": attempts, "attempts_reachable": len(reachable),
            "next_window": reachable[0]["fiscal_year"], "offer_needed_before": reachable[0]["opens"]["value"],
            "scorer_factor": round(factor, 4), "slack_days": slack,
            "formula": "factor = min(1, (opt_start + ceiling − max(as_of + lag, opt_start)) / ceiling)",
            "assumptions": {"hiring_lag_days": lab(lag, INPUT), "unemployment_ceiling_days": lab(ceiling, INPUT),
                            "opt_start_date": lab(start.isoformat(), INPUT), "opt_end_date": lab(end.isoformat(), INPUT)}}


# ── national OEWS (record): stdlib xlsx reader ──────────────────────────────
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col(ref):
    return re.match(r"[A-Z]+", ref).group()


def load_oews(path=OEWS_PATH):
    """Return {occ_code: row} for detailed occupations. Conformance failures halt (exit 4)."""
    try:
        z = zipfile.ZipFile(path)
        shared = [''.join(t.text or '' for t in si.iter('{%s}t' % _NS['m']))
                  for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS)]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as e:
        raise Stop(4, f"OEWS file unreadable: {path} ({type(e).__name__}: {e})")
    rows = []
    for r in sheet.find("m:sheetData", _NS):
        cells = {}
        for c in r:
            v = c.find("m:v", _NS)
            if v is None:
                inline = c.find("m:is", _NS)
                val = ''.join(t.text or '' for t in inline.iter('{%s}t' % _NS['m'])) if inline is not None else ""
            else:
                val = shared[int(v.text)] if c.get("t") == "s" else v.text
            cells[_col(c.get("r"))] = val
        rows.append(cells)
    if not rows:
        raise Stop(4, "OEWS sheet1 is empty")
    header = rows[0]
    names = {v: k for k, v in header.items()}
    missing = [c for c in OEWS_REQUIRED if c not in names]
    if missing:
        raise Stop(4, f"OEWS header is missing required columns {missing} — schema changed, refusing to guess")
    out = {}
    for cells in rows[1:]:
        rec = {n: cells.get(col, "") for n, col in names.items()}
        if rec["O_GROUP"] != "detailed":
            continue
        if rec["AREA_TITLE"] != "U.S.":
            raise Stop(4, f"OEWS row for {rec['OCC_CODE']} has AREA_TITLE {rec['AREA_TITLE']!r}, expected 'U.S.' (national file)")
        out[rec["OCC_CODE"]] = rec
    return out


def parse_pct(value):
    """'*' / '#' / '' -> None. BLS uses '#' for wages at or above the top-code cap."""
    text = str(value or "").strip().replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def ladder(oews_row):
    """[(pct, value)] or (None, reason). Percentiles must ascend strictly."""
    pts = [(p, parse_pct(oews_row.get(col))) for p, col in KNOWN_PCTS]
    bad = [p for p, v in pts if v is None]
    if bad:
        return None, f"OEWS percentile(s) {bad} suppressed or top-coded for {oews_row['OCC_CODE']}"
    vals = [v for _, v in pts]
    if any(b <= a for a, b in zip(vals, vals[1:])):
        return None, f"OEWS percentiles for {oews_row['OCC_CODE']} do not ascend — conformance failure"
    return pts, None


def bracket(wage, pts, thresholds):
    """Which OEWS percentile interval holds `wage`, and the wage-level range that interval allows.

    The wage's percentile q is only known to lie in [q_lo, q_hi). Level = number of
    thresholds t with t <= q. So level_min counts t <= q_lo and level_max counts t < q_hi.
    """
    q_lo, q_hi = 0, 100
    for p, v in pts:
        if wage >= v:
            q_lo = p
        else:
            q_hi = p
            break
    lmin = sum(1 for t in thresholds if t <= q_lo)
    lmax = sum(1 for t in thresholds if t < q_hi)
    return {"pct_interval": [q_lo, q_hi], "level_min": lmin, "level_max": lmax,
            "entries_min": ENTRIES[lmin], "entries_max": ENTRIES[lmax]}


def level_text(lmin, lmax):
    name = lambda n: "below I" if n == 0 else "I II III IV".split()[n - 1]
    return name(lmin) if lmin == lmax else f"{name(lmin)}–{name(lmax)}"


# ── G3: SOC map (your-input, human-confirmed) ───────────────────────────────
def load_soc_map(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    fams = []
    for fam in doc["families"]:
        fams.append({**fam, "_re": re.compile(fam["title_pattern"], re.I)})
    return doc, fams


def family_for(title, fams):
    for fam in fams:
        if fam["_re"].search(title):
            return fam
    return None


def soc_assessment(wage_floor, wage_ceiling, fam, oews):
    """Per plausible SOC: the bracket of the posted floor and ceiling under each rule."""
    per_soc = []
    for s in fam["socs"]:
        code = s["soc"]
        row = oews.get(code)
        entry = {"soc": code, "why_plausible": lab(s["why"], s.get("source", INPUT))}
        if row is None:
            entry.update(status="missing", reason=f"no detailed national OEWS row for {code}")
            per_soc.append(entry)
            continue
        pts, why = ladder(row)
        if pts is None:
            entry.update(status="missing", reason=why)
            per_soc.append(entry)
            continue
        entry.update(status="ok", occ_title=lab(row["OCC_TITLE"], REC),
                     ladder=lab({str(p): v for p, v in pts}, REC, file="national_M2024_dl.xlsx (May 2024, U.S.)"),
                     rules={})
        for rname, rule in RULES.items():
            entry["rules"][rname] = {"floor": bracket(wage_floor, pts, rule["thresholds"]),
                                     "ceiling": bracket(wage_ceiling, pts, rule["thresholds"])}
        per_soc.append(entry)
    return per_soc


def lottery_read(per_soc, rule="current"):
    """Conservative read of the posted FLOOR across every plausible SOC (rule = in-force rule)."""
    ok = [s for s in per_soc if s["status"] == "ok"]
    if not ok:
        return {"read": "NO-BRACKET", "why": "no plausible SOC has a usable OEWS ladder"}
    fl = [s["rules"][rule]["floor"] for s in ok]
    worst_min = min(b["level_min"] for b in fl)
    best_max = max(b["level_max"] for b in fl)
    soc_flips = max(b["level_min"] for b in fl) >= 2 and min(b["level_max"] for b in fl) <= 1
    out = {"worst_case_entries": ENTRIES[worst_min], "best_case_entries": ENTRIES[best_max],
           "below_level_I_possible": any(b["level_min"] == 0 for b in fl),
           "socs_considered": [s["soc"] for s in ok],
           "socs_missing": [s["soc"] for s in per_soc if s["status"] != "ok"]}
    if worst_min >= 2:
        out.update(read="CLEARS-LEVEL-II", why="the posted floor reaches at least the Level II proxy under every plausible SOC")
    elif best_max <= 1:
        out.update(read="LEVEL-I-AT-BEST", why="the posted floor reaches at most the Level I proxy under every plausible SOC")
    elif soc_flips:
        out.update(read="SOC-SENSITIVE", why="the SOC the employer files under decides whether the floor earns 1 entry or 2+")
    else:
        out.update(read="BRACKET-UNRESOLVED", why="the floor falls inside an OEWS percentile interval that straddles a level cut-off")
    return out


# ── pay evidence (record) ───────────────────────────────────────────────────
_AMT = r"(\d{2,3}(?:,\d{3})+(?:\.\d{2})?|\d{2,3}(?:\.\d+)?\s?[kK])"
_RANGE_RE = re.compile(r"\$\s?" + _AMT + r"\s*(?:USD\s*)?(?:-|–|—|to)\s*\$?\s?" + _AMT)
_ANNUAL_CUE = re.compile(r"annual|annually|per year|a year|/\s?yr|per annum|base salary|base pay|salary range", re.I)
_HOURLY_CUE = re.compile(r"per hour|an hour|/\s?h(ou)?r\b|hourly", re.I)


def _amount(tok):
    tok = tok.replace(",", "").replace(" ", "")
    if tok[-1] in "kK":
        return float(tok[:-1]) * 1000
    return float(tok)


def html_to_text(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(html.unescape(s or "")))).strip()


def parse_text_pay(text):
    """Strict fallback: one distinct annual USD range quoted from the posting, or a refusal."""
    found = []
    for m in _RANGE_RE.finditer(text or ""):
        ctx = text[max(0, m.start() - 160): m.end() + 80]
        if _HOURLY_CUE.search(ctx) and not _ANNUAL_CUE.search(ctx):
            found.append(("hourly", None, None, ctx))
            continue
        if not _ANNUAL_CUE.search(ctx):
            continue
        found.append(("annual", _amount(m.group(1)), _amount(m.group(2)), ctx))
    annual = {(lo, hi) for kind, lo, hi, _ in found if kind == "annual"}
    if not found:
        return None, "no-pay-found"
    if not annual:
        return None, "non-annual-pay (hourly cue in posting text)"
    if len(annual) > 1:
        return None, f"pay-ambiguous ({len(annual)} distinct annual ranges in the text)"
    lo, hi = annual.pop()
    quote = next(c for k, a, b, c in found if k == "annual" and (a, b) == (lo, hi))
    return {"min": lo, "max": hi, "currency": "USD", "interval": "annual (text cue)",
            "method": "parsed-text", "quote": quote.strip()}, None


def structured_pay(ats, raw):
    """Read the ATS's own pay field. Returns (pay, reason) — pay None means 'not in a structured field'."""
    if ats == "greenhouse":
        rs = raw.get("pay_input_ranges") or []
        if not rs:
            return None, "no structured pay field"
        cur = {r.get("currency_type") for r in rs}
        if cur != {"USD"}:
            return None, f"non-USD pay {sorted(c or '?' for c in cur)}"
        lo = min(r["min_cents"] for r in rs) / 100
        hi = max(r["max_cents"] for r in rs) / 100
        return {"min": lo, "max": hi, "currency": "USD", "interval": "unstated (Greenhouse pay_input_ranges)",
                "method": "structured", "range_titles": [html_to_text(r.get("title")) for r in rs],
                "n_ranges": len(rs)}, None
    if ats == "lever":
        sr = raw.get("salaryRange")
        if not sr:
            return None, "no structured pay field"
        if sr.get("currency") != "USD":
            return None, f"non-USD pay {sr.get('currency')}"
        if sr.get("interval") != "per-year-salary":
            return None, f"non-annual-pay ({sr.get('interval')})"
        return {"min": float(sr["min"]), "max": float(sr["max"]), "currency": "USD", "interval": "per-year-salary",
                "method": "structured"}, None
    if ats == "ashby":
        comps = [c for c in ((raw.get("compensation") or {}).get("summaryComponents") or [])
                 if c.get("compensationType") == "Salary"]
        if not comps:
            return None, "no structured pay field"
        c = comps[0]
        if c.get("currencyCode") != "USD":
            return None, f"non-USD pay {c.get('currencyCode')}"
        if c.get("interval") != "1 YEAR":
            return None, f"non-annual-pay ({c.get('interval')})"
        if c.get("minValue") is None or c.get("maxValue") is None:
            return None, "structured pay field has no min/max"
        return {"min": float(c["minValue"]), "max": float(c["maxValue"]), "currency": "USD", "interval": "1 YEAR",
                "method": "structured"}, None
    return None, f"unsupported ATS {ats!r}"


def pay_evidence(ats, raw):
    pay, why = structured_pay(ats, raw)
    if pay is None and why == "no structured pay field":
        pay, why = parse_text_pay(raw.get("text", ""))
    if pay is None:
        return None, why
    if not (PAY_MIN <= pay["min"] <= pay["max"] <= PAY_MAX):
        return None, f"pay outside sanity bounds or min > max ({pay['min']:.0f}–{pay['max']:.0f})"
    if pay["min"] < 1000:
        return None, "non-annual-pay (amount looks hourly)"
    return pay, None


# ── snapshot hygiene: postings carry HR contact emails/phones; the mode needs neither ──
# Same patterns as scripts/pii-scan.mjs, so a stored snapshot passes the repo's PII scan.
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}")
GH_PAY_KEYS = ("min_cents", "max_cents", "currency_type", "title")


def redact(text):
    return _PHONE.sub("[phone redacted]", _EMAIL.sub("[email redacted]", text or ""))


def slim_posting(p):
    """Keep only what pay evidence and the report read; redact contact data from posting text."""
    out = dict(p)
    if "text" in out:
        out["text"] = redact(out["text"])
    if "pay_input_ranges" in out:
        out["pay_input_ranges"] = [{k: r.get(k) for k in GH_PAY_KEYS} for r in out["pay_input_ranges"] or []]
    if out.get("compensation") is not None:
        out["compensation"] = {"summaryComponents": (out["compensation"] or {}).get("summaryComponents") or []}
    return out


def redact_snapshot(path):
    """Apply slim_posting to a snapshot written before v0.1.0's redaction landed (logged in the run log)."""
    with open(path, encoding="utf-8") as f:
        snap = json.load(f)
    for b in snap["boards"].values():
        b["postings"] = [slim_posting(p) for p in b.get("postings", [])]
    snap["redacted"] = "slim_posting() applied after the run: contact emails/phones redacted, Greenhouse blurbs dropped"
    write_json(path, snap)


# ── G2: board fetch (only with --live) ──────────────────────────────────────
def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return r.status, json.load(r)


def fetch_board(ats, slug, title_res):
    """List the board; for data-title postings only, keep the fields pay evidence needs."""
    url = LIST_ENDPOINTS[ats].format(slug=slug)
    try:
        status, body = _get(url)
    except urllib.error.HTTPError as e:
        return {"url": url, "http_status": e.code, "error": f"HTTP {e.code}", "postings_total": 0, "postings": []}
    except Exception as e:
        return {"url": url, "http_status": None, "error": f"{type(e).__name__}: {e}", "postings_total": 0, "postings": []}
    if ats == "greenhouse":
        jobs = body.get("jobs", [])
        items = [(j.get("title") or "", (j.get("location") or {}).get("name") or "", j.get("absolute_url"), j) for j in jobs]
    elif ats == "lever":
        jobs = body
        items = [(j.get("text") or "", (j.get("categories") or {}).get("location") or "", j.get("hostedUrl"), j) for j in jobs]
    else:
        jobs = body.get("jobs", [])
        items = [(j.get("title") or "", j.get("location") or "", j.get("jobUrl"), j) for j in jobs]
    postings = []
    for title, loc, purl, j in items:
        if not any(r.search(title) for r in title_res):
            continue
        p = {"title": title, "location": loc, "url": purl}
        if ats == "greenhouse":
            try:
                _, d = _get(GH_DETAIL.format(slug=slug, id=j["id"]))
                p.update(pay_input_ranges=d.get("pay_input_ranges") or [], text=html_to_text(d.get("content")),
                         first_published=d.get("first_published"), updated_at=d.get("updated_at"))
            except Exception as e:
                p.update(detail_error=f"{type(e).__name__}: {e}")
        elif ats == "lever":
            p.update(salaryRange=j.get("salaryRange"),
                     text=" ".join([j.get("descriptionPlain") or "", j.get("additionalPlain") or ""]))
        else:
            p.update(compensation=j.get("compensation"), text=html_to_text(j.get("descriptionHtml")))
        postings.append(slim_posting(p))
    return {"url": url, "http_status": status, "error": None, "postings_total": len(items), "postings": postings}


# ── sponsorship (record) ────────────────────────────────────────────────────
def tier_of(approvals, rate):
    if approvals >= 50 and rate >= 90:
        return "Proven", 0.90
    if approvals >= 10:
        return "Likely", 0.60
    if approvals >= 1:
        return "Possible", 0.40
    return "None", 0.00


def load_sponsors(names):
    out = {}
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["company_name"] in names:
                out[row["company_name"]] = {k: row.get(k, "") for k in KEEP_COLS}
    return out


def sponsorship(row):
    if row is None:
        return {"tier": "None", "p": 0.0, "approvals": 0, "approval_rate": None, "basis": "no exact company_name row in the 80 Days CSV"}
    try:
        approvals = int(float(row["Total Approvals"] or 0))
        rate = float(row["Approval_Rate"]) if row["Approval_Rate"] else 0.0
    except ValueError:
        approvals, rate = 0, 0.0
    tier, p = tier_of(approvals, rate)
    try:
        titles = ast.literal_eval(row["top_job_titles_sponsored"]) if row["top_job_titles_sponsored"] else []
    except (ValueError, SyntaxError):
        titles = []
    med = float(row["median_salary_offered"]) if row["median_salary_offered"] else None
    return {"tier": tier, "p": p, "approvals": approvals, "approval_rate": round(rate, 2),
            "top_titles": titles, "company_median_salary": med,
            "basis": "80 Days CSV row (company-wide counts; no SOC, no title-level wages)"}


# ── output-dir guard: never write over a tracked repo file ──────────────────
ALLOWED_IN_REPO = ("course/2026fa/submissions/AkshitVerma-AV/", "scripts/contrib/2026fa/AkshitVerma-AV-")


def check_out_dir(out_dir):
    rel = os.path.relpath(os.path.abspath(out_dir), REPO).replace(os.sep, "/") + "/"
    if not rel.startswith("../") and not rel.startswith(ALLOWED_IN_REPO):
        raise Stop(2, f"--out-dir {out_dir} is inside the repo but outside this contribution's namespaces {ALLOWED_IN_REPO}")


def relp(path):
    return os.path.relpath(os.path.abspath(path), REPO).replace(os.sep, "/")


# ── run ─────────────────────────────────────────────────────────────────────
def run(args):
    as_of = parse_date(args.as_of) if args.as_of else dt.date.today()
    with open(args.persona, encoding="utf-8") as f:
        persona = json.load(f)
    check_out_dir(args.out_dir)
    if not (args.live or args.snapshot or args.offers):
        raise Stop(2, "nothing to check: pass --live or --snapshot <file> (postings) and/or --offers <file>")
    if args.live and args.snapshot:
        raise Stop(2, "pass --live or --snapshot, not both")

    timeline = timeline_gate(persona, as_of)          # G0 — raises before anything is written
    oews = load_oews()                                # conformance — raises before anything is written
    soc_doc, fams = load_soc_map(args.soc_map)
    title_res = [re.compile(p, re.I) for p in persona["target_title_patterns"]]
    excl_title_res = [re.compile(p, re.I) for p in persona.get("exclude_posting_title_patterns", [])]
    excl_locs = [s.lower() for s in persona.get("exclude_posting_location_patterns", [])]

    snapshot = None
    if args.snapshot:
        with open(args.snapshot, encoding="utf-8") as f:
            snapshot = json.load(f)
        # fetched_at is UTC; as_of is a local date. Compare in local time, or an evening
        # fetch in US time zones lands on "tomorrow" (run-3 replay, 2026-10-19).
        fetched = dt.datetime.fromisoformat(snapshot["fetched_at"]).astimezone().date()
        age = (as_of - fetched).days
        if age > SNAPSHOT_MAX_AGE_DAYS or age < 0:
            raise Stop(5, f"G2 failed: snapshot fetched {fetched} is {age} days from as_of {as_of} (allowed 0–{SNAPSHOT_MAX_AGE_DAYS})")
    os.makedirs(args.out_dir, exist_ok=True)

    rows, audit = [], {"boards_fetched": 0, "boards_unresolved": 0, "postings_total": 0, "data_title_postings": 0,
                       "excluded_title_rule": 0, "excluded_non_us": 0, "entry_eligible_us": 0}
    snap_out = None
    if args.live or snapshot:
        with open(args.boards, encoding="utf-8") as f:
            boards = json.load(f)["boards"]
        sponsors = load_sponsors({b["company_name"] for b in boards})
        snap_out = {"fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds") if args.live else snapshot["fetched_at"],
                    "mode": "live" if args.live else "snapshot", "boards": {}}
        if snapshot:
            snap_out["replayed_from"] = relp(args.snapshot)
        for b in boards:
            name = b["company_name"]
            if b.get("confirmed") is not True:                                   # G1
                rows.append(_board_row(b, "MANUAL-CHECK", "board-not-confirmed (G1: a human must set \"confirmed\": true)"))
                continue
            if b.get("ats") not in LIST_ENDPOINTS:
                rows.append(_board_row(b, "MANUAL-CHECK", f"unsupported ATS {b.get('ats')!r}"))
                continue
            raw = fetch_board(b["ats"], b["slug"], title_res) if args.live else snapshot["boards"].get(name)
            if raw is None:
                raw = {"http_status": None, "error": "company not in snapshot", "postings_total": 0, "postings": []}
            snap_out["boards"][name] = {"ats": b["ats"], "slug": b["slug"], **raw}
            audit["boards_fetched"] += 1
            if raw.get("http_status") != 200 or raw.get("postings_total", 0) == 0:     # G2
                audit["boards_unresolved"] += 1
                why = raw.get("error") or ("board returned zero postings total — not evidence of no openings"
                                           if raw.get("http_status") == 200 else f"HTTP {raw.get('http_status')}")
                rows.append(_board_row(b, "MANUAL-CHECK", f"board unresolved: {why}"))
                continue
            audit["postings_total"] += raw["postings_total"]
            spons = sponsorship(sponsors.get(name))
            for p in raw["postings"]:
                audit["data_title_postings"] += 1
                if any(s in p["location"].lower() for s in excl_locs):
                    audit["excluded_non_us"] += 1
                    continue
                if any(r.search(p["title"]) for r in excl_title_res):
                    audit["excluded_title_rule"] += 1
                    continue
                audit["entry_eligible_us"] += 1
                rows.append(assess_posting(b, p, spons, fams, oews))
    else:
        boards = []

    offers_out = []
    if args.offers:
        with open(args.offers, encoding="utf-8") as f:
            offers = json.load(f)["offers"]
        for o in offers:
            offers_out.append(assess_offer(o, fams, oews))

    # Every live entry-eligible posting is scored, bracketed or not: the scorer judges
    # sponsorship × liveness × timeline and never sees wages (role_quality weight is 0.0).
    # The lottery read sits beside the recommendation; it is not folded into it.
    roles = []
    for i, r in enumerate(rows):
        if r.get("kind") != "posting":
            continue
        r["role_id"] = f"p{i:03d}-{norm_name(r['company'])[:16]}-{norm_name(r['title'])[:16]}"
        roles.append({
            "role_id": r["role_id"], "company": r["company"], "title": r["title"],
            "sponsorship": {"p": r["sponsorship"]["p"], "tier": r["sponsorship"]["tier"], "source": REC,
                            "basis": {"approvals": r["sponsorship"]["approvals"], "approval_rate": r["sponsorship"]["approval_rate"],
                                      "rule": TIER_RULE["version"], "rule_source": INPUT}},
            "liveness": {"factor": 1.0, "source": REC, "basis": "posting present in the board API at fetch time"},
            "timeline": {"factor": timeline["scorer_factor"], "source": INPUT, "basis": timeline["formula"]},
        })
    roles_path = os.path.join(args.out_dir, "roles.json")
    write_json(roles_path, roles)
    if roles:
        proc = subprocess.run(["node", SCORER, roles_path, "--out-dir", args.out_dir], capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            raise Stop(6, f"scorer failed (exit {proc.returncode}): {proc.stderr.strip()}")
        print(proc.stdout.strip())
        with open(os.path.join(args.out_dir, "role-scores.json"), encoding="utf-8") as f:
            scored = {s["role_id"]: s for s in json.load(f)["roles"]}
        for r in rows:
            s = scored.get(r.get("role_id"))
            if s:
                r["scorer"] = {"recommendation": s["recommendation"], "reason": s["reason"], "composite": s["composite"],
                               "arithmetic": s["trace"]["arithmetic"], "source": "role-scores.json"}
    for r in rows + offers_out:
        r["next_action"] = next_action(r)

    if snap_out is not None:
        write_json(os.path.join(args.out_dir, "board-snapshot.json"), snap_out)
    result = build_result(args, as_of, persona, timeline, soc_doc, rows, offers_out, audit, boards)
    write_json(os.path.join(args.out_dir, "lottery-weight.json"), result)
    with open(os.path.join(args.out_dir, "lottery-weight.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(result))
    c = result["counts"]
    reads = " · ".join(f"{k} {v}" for k, v in c["by_read"].items()) or "none"
    print(f"✓ G0 {timeline['attempts_reachable']} reachable lottery window(s) · {audit['entry_eligible_us']} entry-eligible US "
          f"posting(s) of {audit['data_title_postings']} data-titled · bracketed {c['postings_assessed']} ({reads}) · "
          f"MANUAL-CHECK {c['manual_check']} · offers {c['offers']} (bracketed {c['offers_assessed']})")
    print(f"  {os.path.relpath(os.path.join(args.out_dir, 'lottery-weight.json'))}  +  lottery-weight.md")
    return result


def _board_row(b, status, reason):
    return {"kind": "board", "company": b["company_name"], "title": None, "status": status, "reason": reason,
            "board": {"ats": b.get("ats"), "slug": b.get("slug")}}


def assess_posting(b, p, spons, fams, oews):
    row = {"kind": "posting", "company": b["company_name"], "title": p["title"], "location": lab(p["location"], REC),
           "url": p.get("url"), "board": {"ats": b["ats"], "slug": b["slug"]},
           "liveness": lab("live", REC, basis="present in the board API at fetch time; cross-check with npm run ats:liveness"),
           "sponsorship": spons, "status": "ASSESSED", "reason": None}
    if p.get("detail_error"):
        row.update(status="MANUAL-CHECK", reason=f"posting detail fetch failed ({p['detail_error']})")
        return row
    pay, why = pay_evidence(b["ats"], p)
    if pay is None:
        row.update(status="MANUAL-CHECK", reason=why)
        return row
    row["pay"] = lab(pay, REC)
    return _assess_wage(row, p["title"], pay["min"], pay["max"], fams, oews)


def assess_offer(o, fams, oews):
    row = {"kind": "offer", "label": o["label"], "company": o.get("company_name"), "title": o["title"],
           "location": lab(o.get("worksite"), INPUT), "hypothetical": bool(o.get("hypothetical")),
           "status": "ASSESSED", "reason": None}
    base = o.get("base_annual_usd")
    if not isinstance(base, (int, float)) or not (PAY_MIN <= base <= PAY_MAX):
        row.update(status="MANUAL-CHECK", reason=f"base_annual_usd missing or outside {PAY_MIN}–{PAY_MAX}")
        return row
    row["pay"] = lab({"min": float(base), "max": float(base), "currency": "USD", "interval": "annual", "method": "offer"}, INPUT)
    return _assess_wage(row, o["title"], float(base), float(base), fams, oews)


def _assess_wage(row, title, lo, hi, fams, oews):
    fam = family_for(title, fams)
    if fam is None:
        row.update(status="MANUAL-CHECK", reason="title-not-in-soc-map (G3: add a family or skip)")
        return row
    row["soc_family"] = fam["family"]
    if fam.get("confirmed") is not True:
        row.update(status="MANUAL-CHECK", reason=f"soc-map-not-confirmed (G3: family {fam['family']!r} awaits a human)")
        return row
    row["per_soc"] = soc_assessment(lo, hi, fam, oews)
    row["lottery_read"] = lottery_read(row["per_soc"])
    if row["lottery_read"]["read"] == "NO-BRACKET":
        row.update(status="MANUAL-CHECK", reason=row["lottery_read"]["why"])
    return row


NEXT = {
    "CLEARS-LEVEL-II": "apply/tailor if the scorer agrees; the floor already earns 2+ entries under every plausible SOC (national proxy)",
    "SOC-SENSITIVE": "before negotiating, ask the recruiter which SOC code and wage level the LCA will use; the answer decides 1 vs 2+ entries",
    "BRACKET-UNRESOLVED": "the national ladder cannot settle the level; check the OFLC wage table for the worksite before negotiating",
    "LEVEL-I-AT-BEST": "at most 1 entry at this floor; negotiate above the next percentile point, or weigh the single-entry odds",
}
PLAIN = {  # executive-summary wording (P9: no scheme names)
    "CLEARS-LEVEL-II": "reach at least the second step under every plausible job code",
    "SOC-SENSITIVE": "depend on which job code the employer files",
    "BRACKET-UNRESOLVED": "cannot be settled with the national ladder",
    "LEVEL-I-AT-BEST": "reach the first step at most",
}
BELOW_I = (". Under at least one plausible SOC this wage may sit below the Level I prevailing wage: the employer "
           "could then register only with an acceptable alternative wage survey, and the registration counts once")


def next_action(r):
    if r["kind"] == "board":
        return "10 min on the careers page: fix boards.json or strike the company"
    if r["status"] == "MANUAL-CHECK":
        if r["reason"].startswith("soc-map-not-confirmed"):
            return f"a human reviews family {r['soc_family']!r} in soc-map.json, sets confirmed: true, and re-runs (G3)"
        if r["reason"].startswith("title-not-in-soc-map"):
            return "add a title family to soc-map.json with its plausible SOC codes, or skip the role"
        return "read the posting by hand and enter the pay as an offer, or skip it"
    rec = (r.get("scorer") or {}).get("recommendation")
    if rec == "Skip":
        return "none — the scorer skips it; wage level does not rescue a skip"
    lr = r["lottery_read"]
    return NEXT[lr["read"]] + (BELOW_I if lr.get("below_level_I_possible") else "")


def build_result(args, as_of, persona, timeline, soc_doc, rows, offers, audit, boards):
    assessed = [r for r in rows if r["kind"] == "posting" and r["status"] == "ASSESSED"]
    by_read = {}
    for r in assessed:
        by_read[r["lottery_read"]["read"]] = by_read.get(r["lottery_read"]["read"], 0) + 1
    return {
        "recipe": RECIPE, "recipe_version": RECIPE_VERSION, "as_of": as_of.isoformat(),
        "run": {"command": " ".join(sys.argv), "persona": relp(args.persona),
                "persona_fictional": "_fictional" in persona, "boards": relp(args.boards) if boards else None,
                "soc_map": relp(args.soc_map), "offers": relp(args.offers) if args.offers else None,
                "board_mode": "live" if args.live else ("snapshot" if args.snapshot else "none")},
        "sources": {"oews": relp(OEWS_PATH) + " (BLS OEWS May 2024, national, detailed occupations)",
                    "sponsorship": relp(CSV_PATH) + f" (columns kept: {KEEP_COLS})",
                    "scorer": relp(SCORER), "tier_rule": lab(TIER_RULE, INPUT), "rules": RULES,
                    "soc_map_confirmed_by": soc_doc.get("confirmed_by")},
        "timeline": timeline,
        "audit": audit,
        "counts": {"postings_assessed": len(assessed), "by_read": by_read,
                   "manual_check": sum(1 for r in rows if r["status"] == "MANUAL-CHECK"),
                   "offers": len(offers), "offers_assessed": sum(1 for o in offers if o["status"] == "ASSESSED")},
        "rows": rows,
        "offers": offers,
        "never_computed": ["selection probability (no USCIS breakdown of the registration pool by wage level was found as of 2026-10-19)",
                           "the worksite prevailing wage (no OFLC table in the repo)",
                           "the SOC code the employer will file (an employer decision; G3 lists only plausible ones)"],
    }


# ── human report ────────────────────────────────────────────────────────────
def money(x):
    return "—" if x is None else f"${x:,.0f}"


def span(a, b):
    return f"{a}" if a == b else f"{a}–{b}"


def render_md(r):
    t = r["timeline"]
    assessed = [x for x in r["rows"] if x["kind"] == "posting" and x["status"] == "ASSESSED"]
    manual = [x for x in r["rows"] if x["status"] == "MANUAL-CHECK"]
    a = r["audit"]
    L = []
    L.append(f"# Lottery-weight check — {r['as_of']}\n")
    L.append("## Executive summary\n")
    L.append("**What this is.** Since spring 2026, the H-1B lottery gives an employer's registration more "
             "chances when the offered salary sits higher on the government's four-step wage ladder: one entry at "
             "the bottom step, up to four at the top. This report takes data-analyst and data-engineer job postings "
             "that are open today at companies with a strong sponsorship record, reads the pay range each one publishes, "
             "and shows which steps of that ladder the pay could reach.\n")
    L.append("**Why read it.** The step depends on a job code the employer picks and on local wages, and you "
             "see neither. So every answer here is a range, worked out under each job code the employer could "
             "reasonably use. Where the code alone changes the answer, the report tells you what to ask the recruiter.\n")
    reads = "; ".join(f"{v} {PLAIN[k]}" for k, v in r["counts"]["by_read"].items())
    reads = f"at their posted minimum pay, {reads}" if reads else "none could be placed on the ladder yet"
    L.append(f"**What it found.** You can reach **{t['attempts_reachable']}** lottery round(s) before your work "
             f"permission ends; the next one opens around {t['offer_needed_before']}, and the employer needs your "
             f"accepted offer before then. Of {a['data_title_postings']} data-titled postings on the checked boards, "
             f"{a['entry_eligible_us']} are open, US-based, and not senior, intern or contract roles; {reads}. "
             f"{len(manual)} item(s) need a human look. No chance of winning is calculated anywhere: no published count "
             "of registrations at each step was found.\n")
    L.append("This report is for the student. The machine log is `lottery-weight.json` beside it.\n")

    L.append("## Your lottery rounds (gate G0)\n")
    L.append("| Fiscal year | Registration opens (assumed?) | Reachable | Why not |")
    L.append("|---|---|---|---|")
    for x in t["attempts"]:
        L.append(f"| FY{x['fiscal_year']} | {x['opens']['value']}{' (assumed)' if x['opens'].get('assumed') else ''} | "
                 f"{'yes' if x['reachable'] else 'no'} | {'; '.join(x['why_not']) or '—'} |")
    L.append(f"\nWork authorization through **{t['authorized_through']['value']}** ({t['authorized_through']['basis']}; your-input). "
             f"STEM OPT also requires an E-Verify employer, which this report does not check.\n")

    L.append("## Postings (open today, entry-eligible, US)\n")
    if assessed:
        L.append("| Company | Posting | Location | Posted base (source) | Lottery read (floor, every plausible SOC) | Entries at floor | Scorer | Next action |")
        L.append("|---|---|---|---|---|---|---|---|")
        for x in assessed:
            pay, lr = x["pay"]["value"], x["lottery_read"]
            sc = x.get("scorer") or {}
            L.append(f"| {x['company']} | [{x['title']}]({x['url']}) | {x['location']['value']} | "
                     f"{money(pay['min'])}–{money(pay['max'])} ({pay['method']}) | **{lr['read']}** | "
                     f"{span(lr['worst_case_entries'], lr['best_case_entries'])} | {sc.get('recommendation', '—')} "
                     f"({sc.get('composite', '—')}) | {x['next_action']} |")
    else:
        L.append("_No open entry-eligible US posting reached the wage check._")
    L.append("")
    for x in assessed + [o for o in r["offers"] if o["status"] == "ASSESSED"]:
        L.append(_soc_table(x))

    if r["offers"]:
        L.append("## Offers and scenarios you entered\n")
        L.append("| Scenario | Title | Worksite | Base | Lottery read | Entries | Status | Next action |")
        L.append("|---|---|---|---|---|---|---|---|")
        for o in r["offers"]:
            lr = o.get("lottery_read") or {}
            ent = span(lr["worst_case_entries"], lr["best_case_entries"]) if "worst_case_entries" in lr else "—"
            base = money(o["pay"]["value"]["min"]) if o.get("pay") else "—"
            L.append(f"| {o['label']}{' (hypothetical)' if o.get('hypothetical') else ''} | {o['title']} | "
                     f"{o['location']['value'] or '—'} | {base} | {lr.get('read', '—')} | {ent} | "
                     f"{o['status']}{(': ' + o['reason']) if o.get('reason') else ''} | {o['next_action']} |")
        L.append("")

    L.append("## Needs a human look\n")
    if manual:
        L.append("| Company | Posting / item | Location | Pay found | Reason | Next action |")
        L.append("|---|---|---|---|---|---|")
        for x in manual:
            name = x.get("label") or x.get("title") or "(whole board)"
            if x.get("url"):
                name = f"[{name}]({x['url']})"
            pay = (x.get("pay") or {}).get("value")
            pay_s = f"{money(pay['min'])}–{money(pay['max'])} ({pay['method']})" if pay else "—"
            loc = (x.get("location") or {}).get("value") or "—"
            L.append(f"| {x.get('company') or '—'} | {name} | {loc} | {pay_s} | {x['reason']} | "
                     f"{x.get('next_action', 'enter it again with a usable value')} |")
    else:
        L.append("_Nothing._")
    L.append("")

    L.append("## What this report cannot tell you\n")
    L.append("- **The real wage step.** The ladder used here is the *national* one from May 2024. The government's "
             "table for your worksite (July 2026 – June 2027, built on May 2025 data) is not in the repo. In expensive "
             "cities local wages run higher, so these steps are likely **too generous** there.")
    L.append("- **The job code.** The employer's immigration lawyer chooses it after the offer. The codes listed are "
             "the plausible ones a human approved, not the one that will be filed.")
    L.append("- **Your odds.** Entries are not odds; no published count of the registration pool by step was found.")
    L.append("- **Pay you will be offered.** A posted range is not an offer. The floor is used because an offer can land there.")
    L.append("- **Company median salary** in the sponsorship data covers *all* sponsored titles (mostly software "
             "engineers). It is shown for context and never compared with a data-role posting.\n")

    L.append("## Human gate G4\n")
    L.append("- [ ] I read every `parsed-text` quote below and it matches the posting.")
    L.append("- [ ] I checked the plausible job codes for each family (gate G3) before trusting any read.")
    L.append("- Signed: ______________________ Date: __________\n")

    L.append("## Run record\n")
    L.append(f"- Recipe `{r['recipe']}` v{r['recipe_version']} · as_of {r['as_of']} · board mode {r['run']['board_mode']}")
    L.append(f"- Persona `{r['run']['persona']}` (fictional: {r['run']['persona_fictional']}) · SOC map `{r['run']['soc_map']}` "
             f"(confirmed by: {r['sources']['soc_map_confirmed_by'] or 'nobody yet'})")
    L.append(f"- Wage ladder `{r['sources']['oews']}` · sponsorship `{relp(CSV_PATH)}` · scorer `{r['sources']['scorer']}`")
    L.append(f"- Audit: boards fetched {a['boards_fetched']} (unresolved {a['boards_unresolved']}) · postings on boards "
             f"{a['postings_total']} · data-titled {a['data_title_postings']} · excluded senior/intern/contract "
             f"{a['excluded_title_rule']} · excluded non-US {a['excluded_non_us']} · entry-eligible US {a['entry_eligible_us']}")
    if a["data_title_postings"]:
        L.append(f"- Skip before the scorer: {a['data_title_postings'] - a['entry_eligible_us']}/{a['data_title_postings']} data-titled "
                 "postings dropped by the title and location rules (the scorer's own skip rate counts only what reached it)")
    L.append("- Scorer inputs: sponsorship (record), liveness (record), timeline (your-input). Fit is NOT scored, so each "
             "composite is sponsorship alone (tier p × 0.35 × gates); a Proven sponsor scores 0.315, just over the 0.30 "
             "Apply threshold, and a Likely sponsor (0.21) cannot reach Apply without a fit score")
    L.append(f"- Scorer timeline factor {t['scorer_factor']} (slack {t['slack_days']} days; {t['formula']})")
    quotes = [x for x in r["rows"] if x["kind"] == "posting" and (x.get("pay") or {}).get("value", {}).get("method") == "parsed-text"]
    if quotes:
        L.append("\n### Parsed-text pay quotes (verify at G4)\n")
        for x in quotes:
            L.append(f"- **{x['company']} — {x['title']} ({x['location']['value']})**: \"…{x['pay']['value']['quote']}…\"")
    return "\n".join(L) + "\n"


def _soc_table(x):
    pay = x["pay"]["value"]
    head = f"### {x.get('company') or x.get('label')} — {x['title']} · floor {money(pay['min'])}"
    if pay["max"] != pay["min"]:
        head += f" / ceiling {money(pay['max'])}"
    L = [head + f" · family `{x['soc_family']}`\n",
         "| SOC | Occupation (OEWS) | P10 · P25 · P50 · P75 · P90 | Floor percentile | Level now | Entries now | Level if DOL proposal took effect | Why plausible |",
         "|---|---|---|---|---|---|---|---|"]
    for s in x["per_soc"]:
        if s["status"] != "ok":
            L.append(f"| {s['soc']} | — | — | — | missing | — | — | {s['reason']} |")
            continue
        ld = s["ladder"]["value"]
        fl, nprm = s["rules"]["current"]["floor"], s["rules"]["dol-nprm-2026"]["floor"]
        q = fl["pct_interval"]
        ent = span(fl["entries_min"], fl["entries_max"])
        L.append(f"| {s['soc']} | {s['occ_title']['value']} | " + " · ".join(money(ld[k]) for k in ("10", "25", "50", "75", "90"))
                 + f" | P{q[0]}–P{q[1]} | {level_text(fl['level_min'], fl['level_max'])} | {ent} | "
                 f"{level_text(nprm['level_min'], nprm['level_max'])} | {s['why_plausible']['value']} ({s['why_plausible']['source']}) |")
    return "\n".join(L) + "\n"


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=lambda o: None)
        f.write("\n")


def main(argv=None):
    # Windows pipes default to cp1252, which cannot print the scorer's "✓" (run-1, 2026-10-19).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--persona", required=True)
    ap.add_argument("--soc-map", required=True, help="soc-map.json (G3, human-confirmed families)")
    ap.add_argument("--boards", default=os.path.join(HERE, "boards.json"))
    ap.add_argument("--live", action="store_true", help="fetch boards now (network)")
    ap.add_argument("--snapshot", help="replay a saved board-snapshot.json instead of fetching")
    ap.add_argument("--offers", help="offers.json: offers or scenarios you enter by hand")
    ap.add_argument("--as-of", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    try:
        run(args)
    except Stop as e:
        print(f"✗ {e}", file=sys.stderr)
        return e.code
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"✗ input error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
