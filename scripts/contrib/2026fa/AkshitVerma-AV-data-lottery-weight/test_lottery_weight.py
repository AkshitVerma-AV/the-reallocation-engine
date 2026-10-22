#!/usr/bin/env python3
"""Offline tests for lottery_weight.py (no network). Run from the repo root:

    python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-data-lottery-weight -p "test_*.py"

The wage-ladder tests read the real shipped file data/bls/oesm24nat/national_M2024_dl.xlsx,
so a change to that file shows up here. The end-to-end tests call the real
scripts/score/role-scorer.mjs (needs node); nothing re-implements the scorer.
"""

import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lottery_weight as L  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
PERSONA = os.path.join(FIX, "persona-jack-spencer.json")
PERSONA_NO_STEM = os.path.join(FIX, "persona-no-stem.json")
SOC_MAP = os.path.join(HERE, "soc-map.json")
CUR = L.RULES["current"]["thresholds"]
NPRM = L.RULES["dol-nprm-2026"]["thresholds"]
LADDER = [(10, 100.0), (25, 200.0), (50, 300.0), (75, 400.0), (90, 500.0)]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def soc_map_copy(tmp, confirmed):
    """A copy of the shipped map with every family's G3 flag forced — tests never depend on the real gate's state."""
    doc = load(SOC_MAP)
    for fam in doc["families"]:
        fam["confirmed"] = confirmed
    doc["confirmed_by"] = "unit test (not a human gate)" if confirmed else None
    path = os.path.join(tmp, f"soc-map-{'confirmed' if confirmed else 'unconfirmed'}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f)
    return path


def quiet_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = L.main(argv)
    return code, out.getvalue(), err.getvalue()


class Bracket(unittest.TestCase):
    def test_below_p10_is_below_level_one(self):
        b = L.bracket(99, LADDER, CUR)
        self.assertEqual((b["pct_interval"], b["level_min"], b["level_max"]), ([0, 10], 0, 0))
        # below Level I is still registrable with an alternative wage source, entered once — never 0 entries
        self.assertEqual((b["entries_min"], b["entries_max"]), (1, 1))

    def test_between_p25_and_p50_is_one_or_two(self):
        b = L.bracket(250, LADDER, CUR)
        self.assertEqual((b["level_min"], b["level_max"], b["entries_min"], b["entries_max"]), (1, 2, 1, 2))

    def test_exactly_at_median_counts_as_reached(self):
        b = L.bracket(300, LADDER, CUR)
        self.assertEqual((b["pct_interval"], b["level_min"], b["level_max"]), ([50, 75], 3, 4))

    def test_at_or_above_p90_is_level_four(self):
        self.assertEqual(L.bracket(500, LADDER, CUR)["level_min"], 4)
        self.assertEqual(L.bracket(10**6, LADDER, CUR)["level_max"], 4)

    def test_p10_to_p25_cannot_rule_out_below_level_one(self):
        b = L.bracket(150, LADDER, CUR)
        self.assertEqual((b["level_min"], b["level_max"]), (0, 1))

    def test_nprm_moves_cutoffs_up(self):
        b = L.bracket(350, LADDER, NPRM)  # P50–P75 under 34/52/70/88
        self.assertEqual((b["level_min"], b["level_max"]), (1, 3))
        self.assertEqual(L.bracket(250, LADDER, NPRM)["level_max"], 1)

    def test_ladder_refuses_top_coded_or_non_ascending(self):
        row = {"OCC_CODE": "99-9999", "A_PCT10": "1", "A_PCT25": "2", "A_MEDIAN": "3", "A_PCT75": "4", "A_PCT90": "#"}
        pts, why = L.ladder(row)
        self.assertIsNone(pts)
        self.assertIn("suppressed or top-coded", why)
        row["A_PCT90"] = "3"
        pts, why = L.ladder(row)
        self.assertIsNone(pts)
        self.assertIn("do not ascend", why)


class RealLadder(unittest.TestCase):
    """The four reads, checked against the shipped national OEWS file."""

    @classmethod
    def setUpClass(cls):
        cls.oews = L.load_oews()
        cls.fams = {f["family"]: f for f in L.load_soc_map(SOC_MAP)[1]}

    def read(self, family, wage):
        return L.lottery_read(L.soc_assessment(wage, wage, self.fams[family], self.oews))

    def test_oews_file_passes_conformance(self):
        self.assertGreater(len(self.oews), 700)
        self.assertEqual(self.oews["15-2051"]["A_MEDIAN"], "112590")

    def test_85k_data_analyst_is_soc_sensitive(self):
        r = self.read("data-analyst", 85000)
        self.assertEqual(r["read"], "SOC-SENSITIVE")
        self.assertEqual((r["worst_case_entries"], r["best_case_entries"]), (1, 4))
        self.assertTrue(r["below_level_I_possible"])

    def test_140k_data_engineer_clears_level_two(self):
        self.assertEqual(self.read("data-engineer", 140000)["read"], "CLEARS-LEVEL-II")

    def test_72k_bi_analyst_is_level_one_at_best(self):
        r = self.read("business-intelligence", 72000)
        self.assertEqual(r["read"], "LEVEL-I-AT-BEST")
        self.assertEqual(r["best_case_entries"], 1)

    def test_112k_analytics_engineer_is_unresolved_not_guessed(self):
        r = self.read("analytics-engineer", 112000)
        self.assertEqual(r["read"], "BRACKET-UNRESOLVED")
        self.assertEqual((r["worst_case_entries"], r["best_case_entries"]), (1, 2))

    def test_read_uses_the_floor_not_the_ceiling(self):
        # a $112k–$168k analytics-engineer range: the ceiling alone would clear Level II
        per = L.soc_assessment(112000, 168000, self.fams["analytics-engineer"], self.oews)
        self.assertEqual(L.lottery_read(per)["read"], "BRACKET-UNRESOLVED")
        self.assertTrue(all(s["rules"]["current"]["ceiling"]["level_min"] >= 3 for s in per))

    def test_missing_soc_is_reported_not_dropped(self):
        fam = {"family": "x", "socs": [{"soc": "00-0000", "why": "test", "source": "your-input"},
                                       {"soc": "15-2051", "why": "test", "source": "record"}]}
        per = L.soc_assessment(90000, 90000, fam, self.oews)
        self.assertEqual(per[0]["status"], "missing")
        r = L.lottery_read(per)
        self.assertEqual(r["socs_missing"], ["00-0000"])

    def test_oews_schema_change_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.xlsx")
            with zipfile.ZipFile(bad, "w") as z:
                z.writestr("xl/sharedStrings.xml",
                           '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                           '<si><t>OCC_CODE</t></si></sst>')
                z.writestr("xl/worksheets/sheet1.xml",
                           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                           '<row r="1"><c r="A1" t="s"><v>0</v></c></row></sheetData></worksheet>')
            with self.assertRaises(L.Stop) as cm:
                L.load_oews(bad)
            self.assertEqual(cm.exception.code, 4)


class Pay(unittest.TestCase):
    def test_text_range_with_annual_cue(self):
        pay, why = L.parse_text_pay("The base salary range for this position is $140k - $180k annually.")
        self.assertIsNone(why)
        self.assertEqual((pay["min"], pay["max"], pay["method"]), (140000, 180000, "parsed-text"))
        self.assertIn("$140k - $180k", pay["quote"])

    def test_text_range_with_html_mdash(self):
        text = L.html_to_text("Base Pay Range For US Locations: $112,000 &amp;mdash; $168,000 USD")
        pay, why = L.parse_text_pay(text)
        self.assertEqual((pay["min"], pay["max"]), (112000, 168000), why)

    def test_hourly_text_refused(self):
        pay, why = L.parse_text_pay("Pay: $40,000 - $55,000 per hour equivalent, paid hourly.")
        self.assertIsNone(pay)
        self.assertTrue(why.startswith("non-annual-pay"))

    def test_two_ranges_refused_as_ambiguous(self):
        pay, why = L.parse_text_pay("Base salary: $90,000 - $110,000 in Chicago; base salary $120,000 - $140,000 in NYC.")
        self.assertIsNone(pay)
        self.assertTrue(why.startswith("pay-ambiguous"))

    def test_range_without_salary_cue_is_not_pay(self):
        pay, why = L.parse_text_pay("We raised $100,000 - $200,000 for charity last year.")
        self.assertIsNone(pay)
        self.assertEqual(why, "no-pay-found")

    def test_greenhouse_multiple_ranges_use_lowest_floor(self):
        raw = {"pay_input_ranges": [{"min_cents": 9000000, "max_cents": 12000000, "currency_type": "USD", "title": "NYC"},
                                    {"min_cents": 8500000, "max_cents": 11000000, "currency_type": "USD", "title": "US"}]}
        pay, _ = L.pay_evidence("greenhouse", raw)
        self.assertEqual((pay["min"], pay["max"], pay["n_ranges"]), (85000, 120000, 2))

    def test_non_usd_and_hourly_structured_refused(self):
        self.assertIsNone(L.pay_evidence("greenhouse", {"pay_input_ranges": [
            {"min_cents": 9000000, "max_cents": 12000000, "currency_type": "CAD"}]})[0])
        pay, why = L.pay_evidence("lever", {"salaryRange": {"currency": "USD", "interval": "per-hour-wage", "min": 40, "max": 55}})
        self.assertIsNone(pay)
        self.assertIn("non-annual", why)

    def test_inverted_range_refused(self):
        pay, why = L.pay_evidence("lever", {"salaryRange": {"currency": "USD", "interval": "per-year-salary", "min": 150000, "max": 90000}})
        self.assertIsNone(pay)
        self.assertIn("min > max", why)


class Hygiene(unittest.TestCase):
    def test_slim_posting_redacts_contacts_and_keeps_pay(self):
        # fictional contacts; the non-555 number is assembled at runtime so the repo PII scan stays clean
        p = {"text": "Email workforce.privacy@example.com or call (408) 555-0199 or 408-321-" + "7654. "
                     "The base salary range for this position is $140k - $180k annually.",
             "pay_input_ranges": [{"min_cents": 1, "max_cents": 2, "currency_type": "USD", "title": "US",
                                   "blurb": "<p>write to hr@example.org</p>"}]}
        s = L.slim_posting(p)
        self.assertNotIn("@", s["text"])
        self.assertNotIn("321-7654", s["text"])
        self.assertNotIn("blurb", s["pay_input_ranges"][0])
        self.assertEqual(L.parse_text_pay(s["text"])[0]["min"], 140000)


class Timeline(unittest.TestCase):
    def test_stem_persona_has_three_rounds(self):
        t = L.timeline_gate(load(PERSONA), dt.date(2026, 10, 19))
        self.assertEqual(t["attempts_reachable"], 3)
        self.assertEqual(t["authorized_through"]["value"], "2030-01-22")
        self.assertFalse(t["attempts"][3]["reachable"])

    def test_no_stem_persona_has_one_round(self):
        t = L.timeline_gate(load(PERSONA_NO_STEM), dt.date(2026, 10, 19))
        self.assertEqual(t["attempts_reachable"], 1)
        self.assertEqual(t["next_window"], 2028)

    def test_no_reachable_round_refuses(self):
        # as_of + 60-day lag lands after the only window this persona can use
        with self.assertRaises(L.Stop) as cm:
            L.timeline_gate(load(PERSONA_NO_STEM), dt.date(2027, 1, 15))
        self.assertEqual(cm.exception.code, 3)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")

    def tearDown(self):
        self.tmp.cleanup()

    def argv(self, soc_map, *extra):
        return ["--persona", PERSONA, "--soc-map", soc_map, "--boards", os.path.join(FIX, "boards-fixture.json"),
                "--snapshot", os.path.join(FIX, "board-snapshot-fixture.json"), "--as-of", "2026-10-20",
                "--out-dir", self.out, *extra]

    def test_g3_unconfirmed_brackets_nothing(self):
        code, out, _ = quiet_main(self.argv(soc_map_copy(self.tmp.name, False)))
        self.assertEqual(code, 0)
        r = load(os.path.join(self.out, "lottery-weight.json"))
        self.assertEqual(r["counts"]["postings_assessed"], 0)
        self.assertTrue(all("per_soc" not in x for x in r["rows"]))

    def test_confirmed_run_buckets_and_calls_real_scorer(self):
        code, out, err = quiet_main(self.argv(soc_map_copy(self.tmp.name, True),
                                              "--offers", os.path.join(FIX, "offers-scenario.json")))
        self.assertEqual(code, 0, err)
        r = load(os.path.join(self.out, "lottery-weight.json"))
        a = r["audit"]
        self.assertEqual((a["data_title_postings"], a["excluded_title_rule"], a["excluded_non_us"], a["entry_eligible_us"]), (6, 1, 1, 4))
        rows = {(x["company"], x.get("title")): x for x in r["rows"]}
        self.assertEqual(rows[("KLAVIYO INC", "Data Analyst")]["lottery_read"]["read"], "SOC-SENSITIVE")
        self.assertEqual(rows[("SIGMA COMPUTING INC", "Data Engineer")]["lottery_read"]["read"], "CLEARS-LEVEL-II")
        self.assertEqual(rows[("SIGMA COMPUTING INC", "Data Engineer")]["pay"]["value"]["method"], "parsed-text")
        self.assertEqual(rows[("ZOOX INC", "Data Analyst")]["status"], "MANUAL-CHECK")          # hourly
        self.assertEqual(rows[("KLAVIYO INC", "Business Intelligence Analyst")]["reason"], "no-pay-found")
        self.assertIn("board-not-confirmed", rows[("GUSTO INC", None)]["reason"])                # G1
        self.assertIn("zero postings", rows[("ROKU INC", None)]["reason"])                       # G2 unresolved
        self.assertTrue(os.path.exists(os.path.join(self.out, "role-scores.json")))            # real scorer ran
        scored = load(os.path.join(self.out, "role-scores.json"))["roles"]
        self.assertEqual(len(scored), 4)
        offers = {o["label"]: o for o in r["offers"]}
        self.assertEqual(offers["A"]["lottery_read"]["read"], "SOC-SENSITIVE")
        self.assertEqual(offers["B"]["lottery_read"]["read"], "LEVEL-I-AT-BEST")
        self.assertEqual(offers["D"]["status"], "MANUAL-CHECK")                                  # Product Analyst unmapped
        md = text(os.path.join(self.out, "lottery-weight.md"))
        self.assertTrue(md.splitlines()[2].startswith("## Executive summary"))

    def test_outputs_never_carry_probability_or_pii_columns(self):
        quiet_main(self.argv(soc_map_copy(self.tmp.name, True)))
        blob = text(os.path.join(self.out, "lottery-weight.json")).lower()
        self.assertNotIn('"probability"', blob)
        self.assertNotIn("selection_odds", blob)
        for col in ("phone", "executive_officers", "board_directors"):
            self.assertNotIn(col, blob)

    def test_stale_snapshot_refused(self):
        argv = self.argv(SOC_MAP)
        argv[argv.index("--as-of") + 1] = "2026-11-30"
        code, _, err = quiet_main(argv)
        self.assertEqual(code, 5)
        self.assertFalse(os.path.exists(os.path.join(self.out, "lottery-weight.json")))

    def test_late_evening_utc_fetch_is_not_a_future_snapshot(self):
        # run-3 regression: a fetch at 23:00 local is "tomorrow" in UTC; same-day replay must pass
        snap = load(os.path.join(FIX, "board-snapshot-fixture.json"))
        snap["fetched_at"] = dt.datetime(2026, 10, 19, 23, 0).astimezone().astimezone(dt.timezone.utc).isoformat()
        path = os.path.join(self.tmp.name, "late-snapshot.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f)
        argv = self.argv(SOC_MAP)
        argv[argv.index("--snapshot") + 1] = path
        argv[argv.index("--as-of") + 1] = "2026-10-19"
        code, _, err = quiet_main(argv)
        self.assertEqual(code, 0, err)

    def test_out_dir_inside_repo_namespace_guard(self):
        argv = self.argv(SOC_MAP)
        argv[argv.index("--out-dir") + 1] = os.path.join(L.REPO, "logs")
        code, _, err = quiet_main(argv)
        self.assertEqual(code, 2)
        self.assertIn("outside this contribution's namespaces", err)

    def test_nothing_to_check_is_a_usage_error(self):
        code, _, _ = quiet_main(["--persona", PERSONA, "--soc-map", SOC_MAP, "--out-dir", self.out])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
