#!/usr/bin/env python3
"""Offline tests for network_targets.py — no network calls (urlopen is patched to fail).

Reads the real repo data (80 Days CSV, Form D samples, BLS compact) and the fixtures in
fixtures/, and runs the REAL scorer (scripts/score/role-scorer.mjs) through node.

Run from repo root:
  python3 -m unittest discover -s scripts/contrib/2026fa/AkshitVerma-AV-preopt-data-network-targets -p "test_*.py" -v
"""

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import network_targets as nt  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
PERSONA = os.path.join(FIX, "persona-jack-spencer.json")
EXPIRED = os.path.join(FIX, "persona-expired-opt.json")
BOARDS = os.path.join(FIX, "boards-fixture.json")
SNAPSHOT = os.path.join(FIX, "board-snapshot-fixture.json")
AS_OF = "2026-10-03"
PHONE = re.compile(r"(\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}")  # same pattern as scripts/pii-scan.mjs


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def no_network(*a, **k):
    raise AssertionError("network call attempted in an offline test")


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("urllib.request.urlopen", no_network), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = nt.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class HappyPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="nt-test-")
        cls.out = os.path.join(cls.tmp, "run")
        cls.code, cls.stdout, cls.stderr = run_cli("--persona", PERSONA, "--boards", BOARDS, "--snapshot", SNAPSHOT,
                                                   "--as-of", AS_OF, "--out-dir", cls.out)
        with open(os.path.join(cls.out, "network-targets.json"), encoding="utf-8") as f:
            cls.result = json.load(f)
        cls.by = {c["company"]["value"]: c for c in cls.result["companies"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_exit_zero_and_both_outputs(self):
        self.assertEqual(self.code, 0, self.stderr)
        for f in ("network-targets.json", "network-targets.md", "role-scores.json", "roles.json", "candidates.json", "board-snapshot.json"):
            self.assertTrue(os.path.exists(os.path.join(self.out, f)), f)

    def test_existing_scorer_was_called(self):
        self.assertIn("scored", self.stdout)  # role-scorer.mjs's own console line
        with open(os.path.join(self.out, "role-scores.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["_scorer"], "bayesian-role-scorer")

    def test_buckets(self):
        expect = {"OUTSET MEDICAL INC": "NETWORK", "PINTEREST INC": "APPLY-TAILOR", "OMADA HEALTH INC": "APPLY-TAILOR",
                  "GUSTO INC": "SKIP", "UPSTART NETWORK INC": "SKIP", "BYHEART INC": "SKIP",
                  "KLAVIYO INC": "MANUAL-CHECK", "COURSERA INC": "MANUAL-CHECK", "ZOOX INC": "MANUAL-CHECK",
                  "SIGMA COMPUTING INC": "MANUAL-CHECK"}
        for name, bucket in expect.items():
            self.assertEqual(self.by[name]["bucket"], bucket, f"{name}: {self.by[name]['bucket_reason']}")

    def test_every_candidate_in_exactly_one_bucket(self):
        c = self.result["counts"]
        self.assertEqual(c["candidates"], c["APPLY-TAILOR"] + c["NETWORK"] + c["MANUAL-CHECK"] + c["SKIP"])
        self.assertEqual(len({x["company"]["value"] for x in self.result["companies"]}), c["candidates"])

    def test_unresolved_never_sent_to_scorer(self):
        # role-scorer.mjs defaults a missing liveness to 1.0 — an unresolved company in roles.json would look live.
        with open(os.path.join(self.out, "roles.json"), encoding="utf-8") as f:
            scored = {r["company"] for r in json.load(f)}
        for name in ("KLAVIYO INC", "COURSERA INC", "ZOOX INC", "SIGMA COMPUTING INC"):
            self.assertNotIn(name, scored)
        for r in load(os.path.join(self.out, "roles.json")):
            self.assertIn(r["liveness"]["factor"], (0.0, 1.0))

    def test_empty_board_is_unresolved_not_none(self):
        k = self.by["KLAVIYO INC"]
        self.assertEqual(k["board"]["status"], "unresolved")
        self.assertIn("zero postings", k["bucket_reason"])

    def test_404_is_unresolved(self):
        self.assertIn("404", self.by["COURSERA INC"]["bucket_reason"])

    def test_senior_intern_and_non_us_postings_do_not_count_as_live(self):
        self.assertEqual(self.by["GUSTO INC"]["board"]["status"], "none")
        self.assertEqual(self.by["GUSTO INC"]["board"]["excluded_by_title_rule"], 2)
        self.assertEqual(self.by["UPSTART NETWORK INC"]["board"]["status"], "none")

    def test_contract_student_worker_posting_does_not_count_as_live(self):
        # run-1 regression (v0.1.0): Zoox reached APPLY-TAILOR on "Contract Student Worker - Data Analyst (Part-time)".
        up = self.by["UPSTART NETWORK INC"]
        self.assertEqual(up["board"]["status"], "none")
        self.assertEqual(up["board"]["excluded_by_title_rule"], 1)

    def test_senior_only_evidence_is_flagged_not_bucketed(self):
        # Outset's only sponsored data title is "Staff Data Engineer" -> flagged, still NETWORK (the flag changes no bucket).
        self.assertTrue(self.by["OUTSET MEDICAL INC"]["sponsorship"]["senior_only_evidence"]["value"])
        self.assertEqual(self.by["OUTSET MEDICAL INC"]["bucket"], "NETWORK")
        # Klaviyo's sponsored data title is "Business Intelligence Engineer" -> not flagged.
        self.assertFalse(self.by["KLAVIYO INC"]["sponsorship"]["senior_only_evidence"]["value"])

    def test_funding_requirement_blocks_and_is_reported(self):
        self.assertEqual(self.by["GUSTO INC"]["bucket_reason"], "network-blocked: funding stale")
        self.assertEqual(self.result["counts"]["network_blocked"], 2)
        self.assertEqual(self.by["OUTSET MEDICAL INC"]["funding"]["funding_evidence"]["value"], "recent")

    def test_company_not_in_csv_is_never_scored(self):
        self.assertNotIn("NOT A REAL COMPANY LLC", self.by)
        self.assertEqual(self.result["board_map_unmatched"][0]["company_name"], "NOT A REAL COMPANY LLC")

    def test_values_carry_source_labels(self):
        o = self.by["OUTSET MEDICAL INC"]
        self.assertEqual(o["company"]["source"], "record")
        self.assertEqual(o["sponsorship"]["approvals"]["source"], "record")
        self.assertEqual(o["sponsorship"]["tier"]["source"], "your-input")
        self.assertEqual(self.result["timeline"]["source"], "your-input")

    def test_sponsorship_values_match_csv(self):
        # cross-check against the source file, not against our own code
        import csv
        with open(nt.CSV_PATH, encoding="utf-8", newline="") as f:
            row = next(r for r in csv.DictReader(f) if r["company_name"] == "OUTSET MEDICAL INC")
        self.assertEqual(self.by["OUTSET MEDICAL INC"]["sponsorship"]["approvals"]["value"], float(row["Total Approvals"]))

    def test_no_phone_numbers_in_outputs(self):
        for f in os.listdir(self.out):
            with open(os.path.join(self.out, f), encoding="utf-8") as fh:
                self.assertIsNone(PHONE.search(fh.read()), f)

    def test_markdown_report_has_labels_and_sign_off(self):
        md = read(os.path.join(self.out, "network-targets.md"))
        self.assertTrue(md.startswith("# Network targets"))
        self.assertIn("[record]", md)
        self.assertIn("[your-input", md)
        self.assertIn("G3 — human sign-off", md)


class FailureCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nt-fail-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_expired_opt_stops_at_g0_and_writes_nothing(self):
        out = os.path.join(self.tmp, "x")
        code, _, err = run_cli("--persona", EXPIRED, "--boards", BOARDS, "--snapshot", SNAPSHOT, "--as-of", AS_OF, "--out-dir", out)
        self.assertEqual(code, 3)
        self.assertIn("opt_end_date", err)
        self.assertFalse(os.path.exists(out))

    def test_stale_snapshot_stops_at_g2(self):
        code, _, err = run_cli("--persona", PERSONA, "--boards", BOARDS, "--snapshot", SNAPSHOT,
                               "--as-of", "2026-10-20", "--out-dir", os.path.join(self.tmp, "x"))
        self.assertEqual(code, 5)
        self.assertIn("snapshot", err)

    def test_soc_with_no_row_is_missing_not_invented(self):
        p = load(PERSONA)
        p["target_soc"] = ["15-2051.01", "15-1199.00"]
        path = os.path.join(self.tmp, "persona.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(p, f)
        out = os.path.join(self.tmp, "run")
        code, _, err = run_cli("--persona", path, "--boards", BOARDS, "--snapshot", SNAPSHOT, "--as-of", AS_OF, "--out-dir", out)
        self.assertEqual(code, 0, err)
        w = load(os.path.join(out, "network-targets.json"))["wage_context"]
        missing = [x for x in w if x["onet_soc_code"] == "15-1199.00"][0]
        self.assertEqual(missing["status"], "missing")
        self.assertNotIn("annual_median_wage", missing)

    def test_out_dir_inside_repo_outside_namespace_is_refused(self):
        code, _, err = run_cli("--persona", PERSONA, "--boards", BOARDS, "--snapshot", SNAPSHOT, "--as-of", AS_OF,
                               "--out-dir", os.path.join(nt.REPO, "data", "examples"))
        self.assertEqual(code, 2)
        self.assertIn("outside this contribution", err)

    def test_requires_live_or_snapshot(self):
        code, _, err = run_cli("--persona", PERSONA, "--boards", BOARDS, "--as-of", AS_OF, "--out-dir", os.path.join(self.tmp, "x"))
        self.assertEqual(code, 2)


class TitlePatterns(unittest.TestCase):
    """Hand-labeled real strings from top_job_titles_sponsored."""
    def setUp(self):
        p = load(PERSONA)
        self.res = [re.compile(x, re.I) for x in p["target_title_patterns"]]

    def match(self, t):
        return any(r.search(t) for r in self.res)

    def test_true_positives(self):
        for t in ("Data Engineer", "Senior Data Analyst", "Lead BI Engineer", "Director Data Warehousing", "Business Intelligence Analyst"):
            self.assertTrue(self.match(t), t)

    def test_true_negatives(self):
        for t in ("Data Admin", "Data Integrity Specialist", "Software Engineer"):
            self.assertFalse(self.match(t), t)

    def test_borderline_title_matches(self):
        # First pass hand-labeled this real Zoox title as a negative; it contains "Analytics Engineer"
        # and does match. Kept as a match: a domain analytics role a data grad might fit. A human judges.
        self.assertTrue(self.match("Senior AV Safety Data and Analytics Engineer"))

    def test_known_false_negative_is_still_missed(self):
        # Documented gap (CHANGE-BRIEF §4 case 5): analytics consulting titles are not matched.
        self.assertFalse(self.match("Consultant - Analytics"))


if __name__ == "__main__":
    unittest.main()
