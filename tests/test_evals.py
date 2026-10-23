"""Offline regressions for candidate provenance, fixture integrity and live budgets."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evals import run_eval as ev


class FakeProvider:
    """Explicit offline provider substitute, never an actual live invocation."""

    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def post_json(self, url, headers, body, timeout):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return ev._make_mock_response("UNVERIFIABLE")


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.network = patch.object(ev.claimcheck.RealHttpClient, "post_json",
                                    side_effect=AssertionError("Network forbidden in tests")).start()
        self.addCleanup(patch.stopall)

    def capture(self, function, *args, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = function(*args, **kwargs)
        self.network.assert_not_called()
        return result, output.getvalue()

    def fixture_data(self):
        return ev._read_fixture(ev.CLAIMS_FILE), ev._read_fixture(ev.EVIDENCE_FILE)

    def assert_invalid_cases(self, claims, evidence):
        with patch.object(ev, "_read_fixture", side_effect=[claims, evidence]):
            with self.assertRaises(ev.EvalFixtureError):
                ev.load_cases()

    def test_all_candidates_require_abstention_without_human_review(self):
        cases, evidence = ev.load_cases()
        self.assertEqual(len(cases), 8)
        self.assertEqual({case["expected_verdict"] for case in cases}, ev.claimcheck.VALID_VERDICTS)
        self.assertTrue(all(case["allowed_outcomes"] == ["UNVERIFIABLE"] for case in cases))
        self.assertTrue(all(case["provenance_reviewed"] is False for case in cases))
        self.assertTrue(all(item["verified_by_human"] is False for item in evidence.values()))

    def test_default_and_standalone_validation_restore_environment(self):
        for function in (ev.run_mock_tests, ev.run_validation_tests):
            for initial in ({}, {"OPENROUTER_API_KEY": "owner-key-sentinel", "KEEP_ME": "unchanged"}):
                with self.subTest(function=function.__name__, key_present=bool(initial)):
                    with patch.dict(os.environ, initial, clear=True):
                        before = dict(os.environ)
                        (passed, total, failures), output = self.capture(function)
                        self.assertEqual(dict(os.environ), before)
                    self.assertEqual(passed, total)
                    self.assertFalse(failures)
                    self.assertIn("real requests: 0", output)
                    self.assertNotIn("actual=TRUE", output)
                    self.assertNotIn("actual=FALSE", output)
                    self.assertNotIn("actual=MISLEADING", output)
                    self.assertNotIn("owner-key-sentinel", output)

    def test_fixture_rejects_broken_references_and_duplicate_cases(self):
        claims, evidence = self.fixture_data()
        mutations = [
            lambda data: data["cases"][0].update(evidence_ids=["missing"]),
            lambda data: data["cases"][0].update(evidence_ids=["source-01", "source-01"]),
            lambda data: data["cases"][1].update(id=data["cases"][0]["id"]),
            lambda data: data["cases"][1].update(text=data["cases"][0]["text"]),
            lambda data: data["cases"].append(copy.deepcopy(data["cases"][0])),
            lambda data: data["cases"][0].update(expected_verdict="true"),
        ]
        for mutate in mutations:
            broken = copy.deepcopy(claims)
            mutate(broken)
            with self.subTest(mutation=mutations.index(mutate)):
                self.assert_invalid_cases(broken, evidence)

    def test_fixture_flags_cannot_promote_a_factual_oracle(self):
        claims, evidence = self.fixture_data()
        for replacement in ({"provenance_reviewed": True}, {"provenance_reviewed": "false"},
                            {"allowed_outcomes": ["TRUE", "UNVERIFIABLE"]},
                            {"allow_abstain": 1}, {"allowed_outcomes": "UNVERIFIABLE"}):
            with self.subTest(replacement=replacement):
                broken = copy.deepcopy(claims)
                broken["cases"][0].update(replacement)
                self.assert_invalid_cases(broken, evidence)

    def test_fixture_rejects_duplicate_or_invalid_source_records(self):
        claims, evidence = self.fixture_data()
        for mutation in ("duplicate", "missing-metadata"):
            broken = copy.deepcopy(evidence)
            if mutation == "duplicate":
                broken["evidence"].append(copy.deepcopy(broken["evidence"][0]))
            else:
                del broken["evidence"][0]["publisher"]
            with self.subTest(mutation=mutation):
                self.assert_invalid_cases(claims, broken)

    def test_fixture_json_rejects_duplicates_constants_and_excess_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            for text in ('{"schema":"claim-evidence/v1","schema":"claim-evidence/v1"}',
                         '{"schema":"claim-evidence/v1","value":NaN}',
                         '{"schema":"claim-evidence/v1","value":Infinity}',
                         " " * (ev.MAX_FIXTURE_BYTES + 1)):
                with self.subTest(prefix=text[:65]):
                    path.write_text(text)
                    with self.assertRaises(ev.EvalFixtureError):
                        ev._read_fixture(path)

    def test_live_prerequisites_make_zero_attempts(self):
        provider = FakeProvider()
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-fake-key"}, clear=True):
            result, output = self.capture(ev.run_live_tests, client=provider)
            self.assertTrue(result[2])
            self.assertIn("BLOCKED", output)
        for initial in ({}, {"OPENROUTER_API_KEY": ev.MOCK_KEY}):
            with patch.dict(os.environ, initial, clear=True):
                result, _ = self.capture(ev.run_live_tests, confirm_free_allowance=True, client=provider)
                self.assertTrue(result[2])
        self.assertEqual(provider.calls, 0)

    def test_live_loop_with_injected_provider_counts_exactly_eight_attempts(self):
        provider = FakeProvider()
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-fake-key"}, clear=True):
            result, output = self.capture(ev.run_live_tests, confirm_free_allowance=True, client=provider)
        self.assertEqual(result, (8, 8, []))
        self.assertEqual(provider.calls, 8)
        self.assertIn("Live request attempts: 8; cap: 8", output)
        self.assertIn("do not verify TRUE/FALSE/MISLEADING", output)

    def test_live_loop_stops_after_first_provider_failure(self):
        errors = [ev.claimcheck.ProviderHTTPError(status, "do not echo this")
                  for status in (401, 402, 429, 500)]
        errors += [ev.claimcheck.ProviderTimeoutError("do not echo this")]
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-fake-key"}, clear=True):
            for error in errors:
                provider = FakeProvider(error)
                with self.subTest(error=type(error).__name__):
                    result, output = self.capture(ev.run_live_tests, confirm_free_allowance=True, client=provider)
                    self.assertEqual(provider.calls, 1)
                    self.assertEqual(result[:2], (0, 1))
                    self.assertTrue(result[2])
                    self.assertIn("Live request attempts: 1", output)
                    self.assertNotIn("do not echo this", output)

    def test_live_counter_does_not_count_local_preflight_failure(self):
        provider = FakeProvider()
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-fake-key"}, clear=True), \
                patch.object(ev.claimcheck, "check_claim",
                             side_effect=ev.claimcheck.InputValidationError("local")):
            result, output = self.capture(ev.run_live_tests, confirm_free_allowance=True, client=provider)
        self.assertTrue(result[2])
        self.assertEqual(provider.calls, 0)
        self.assertIn("Live request attempts: 0", output)

    def test_budget_wrapper_prevents_a_ninth_request(self):
        provider = FakeProvider()
        client = ev.CountingHttpClient(provider, 100)
        for _ in range(8):
            client.post_json("", {}, {}, 30)
        with self.assertRaises(ev.claimcheck.ConfigurationError):
            client.post_json("", {}, {}, 30)
        self.assertEqual(provider.calls, 8)
        self.assertEqual(client.call_count, 8)

    def test_live_cli_requires_allowance_flag(self):
        with patch.object(ev.sys, "argv", ["run_eval.py", "--live"]), \
                patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-fake-key"}, clear=True):
            result, output = self.capture(ev.main)
        self.assertEqual(result, 1)
        self.assertIn("BLOCKED", output)


if __name__ == "__main__":
    unittest.main()
