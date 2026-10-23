#!/usr/bin/env python3
"""Offline software checks and explicitly gated live candidate evaluation."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import claimcheck

MAX_LIVE_CASES = 8
MAX_FIXTURE_BYTES = 128 * 1024
MOCK_KEY = "mock-test-key-not-real"
EVALS_DIR = Path(__file__).resolve().parent
CLAIMS_FILE = EVALS_DIR / "claims.json"
EVIDENCE_FILE = EVALS_DIR / "evidence.json"


class EvalFixtureError(ValueError):
    """Candidate fixtures failed their local contract."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvalFixtureError("Duplicate fixture JSON key.")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise EvalFixtureError("Nonstandard fixture JSON constant.")


def _read_fixture(path: Path) -> dict[str, Any]:
    try:
        with open(path, "rb") as stream:
            raw = stream.read(MAX_FIXTURE_BYTES + 1)
        if len(raw) > MAX_FIXTURE_BYTES:
            raise EvalFixtureError("Fixture exceeds its size limit.")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvalFixtureError("Cannot read evaluation fixture.") from exc
    if not isinstance(data, dict) or data.get("schema") != "claim-evidence/v1":
        raise EvalFixtureError("Invalid evaluation fixture schema.")
    return data


def _fixture_id(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) is not None


def load_cases() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Validate intended categories; current unreviewed outcomes must abstain."""
    claims_data = _read_fixture(CLAIMS_FILE)
    evidence_data = _read_fixture(EVIDENCE_FILE)
    try:
        evidence = claimcheck.validate_evidence(evidence_data.get("evidence"))
    except claimcheck.ClaimCheckError as exc:
        raise EvalFixtureError("Invalid candidate evidence.") from exc
    if any(not _fixture_id(item["id"]) for item in evidence):
        raise EvalFixtureError("Invalid candidate evidence identifier.")
    evidence_by_id = {item["id"]: item for item in evidence}
    cases = claims_data.get("cases")
    if not isinstance(cases, list) or len(cases) != MAX_LIVE_CASES:
        raise EvalFixtureError("Exactly eight candidate cases are required.")
    seen_ids: set[str] = set()
    seen_claims: set[str] = set()
    categories: set[str] = set()
    required = {"id", "text", "evidence_ids", "expected_verdict", "allow_abstain",
                "provenance_reviewed", "allowed_outcomes", "rationale_for_expected"}
    for case in cases:
        if not isinstance(case, dict) or set(case) != required:
            raise EvalFixtureError("Invalid candidate case fields.")
        case_id = case["id"]
        if not _fixture_id(case_id) or case_id in seen_ids:
            raise EvalFixtureError("Invalid or duplicate candidate identifier.")
        seen_ids.add(case_id)
        try:
            claim = claimcheck.validate_claim(case["text"])
        except claimcheck.ClaimCheckError as exc:
            raise EvalFixtureError("Invalid candidate claim.") from exc
        if claim != case["text"] or claim in seen_claims:
            raise EvalFixtureError("Candidate claims must be distinct and trimmed.")
        seen_claims.add(claim)
        intended = case["expected_verdict"]
        if not isinstance(intended, str) or intended not in claimcheck.VALID_VERDICTS:
            raise EvalFixtureError("Invalid intended verdict category.")
        categories.add(intended)
        ids = case["evidence_ids"]
        if not isinstance(ids, list) or any(not _fixture_id(eid) for eid in ids):
            raise EvalFixtureError("Invalid candidate evidence references.")
        if len(set(ids)) != len(ids) or not set(ids) <= evidence_by_id.keys():
            raise EvalFixtureError("Duplicate or missing candidate evidence reference.")
        if type(case["provenance_reviewed"]) is not bool or case["provenance_reviewed"]:
            raise EvalFixtureError("Bundled candidates must remain explicitly unreviewed.")
        if case["allow_abstain"] is not True or case["allowed_outcomes"] != ["UNVERIFIABLE"]:
            raise EvalFixtureError("Unreviewed candidates must require abstention.")
        rationale = case["rationale_for_expected"]
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 2000:
            raise EvalFixtureError("Missing or unbounded candidate rationale.")
    if categories != set(claimcheck.VALID_VERDICTS):
        raise EvalFixtureError("Candidates must cover all four intended categories.")
    return cases, evidence_by_id


def _make_mock_response(verdict: str,
                        rationale: str = "Synthetic response for software contract testing only.",
                        what_would_settle_it: str = "Independent owner review of relevant evidence.",
                        evidence_ids: list[str] | None = None) -> dict[str, Any]:
    card = {"verdict": verdict, "rationale": rationale,
            "what_would_settle_it": what_would_settle_it,
            "evidence_ids": evidence_ids if evidence_ids is not None else []}
    return {"model": claimcheck.FIXED_MODEL, "choices": [
        {"finish_reason": "stop", "message": {
            "role": "assistant", "content": json.dumps(card)}}]}


class MockHttpClient:
    """Explicit synthetic response; no substring matching or fallback verdict."""

    def __init__(self, response: dict[str, Any] | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.call_count = 0
        self.last_request: dict[str, Any] | None = None

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any],
                  timeout: int) -> dict[str, Any]:
        self.call_count += 1
        self.last_request = {"url": url, "headers": headers, "body": body, "timeout": timeout}
        assert url == claimcheck.OPENROUTER_URL
        assert body.get("model") == claimcheck.FIXED_MODEL
        assert headers.get("Authorization") == f"Bearer {MOCK_KEY}"
        assert timeout == 30
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise AssertionError("No synthetic response configured.")
        return copy.deepcopy(self.response)


class CountingHttpClient:
    """Hard cap on actual request attempts, including provider failures."""

    def __init__(self, client: Any, limit: int):
        self.client = client
        self.limit = min(limit, MAX_LIVE_CASES)
        self.call_count = 0

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any],
                  timeout: int) -> dict[str, Any]:
        if self.call_count >= self.limit:
            raise claimcheck.ConfigurationError("Live request limit reached.")
        self.call_count += 1
        return self.client.post_json(url, headers, body, timeout)


def run_mock_tests(verbose: bool = False) -> tuple[int, int, list[str]]:
    cases, evidence_by_id = load_cases()
    passed, calls = 0, 0
    failures: list[str] = []
    print("OFFLINE MOCKS — software behavior only; no factual or live verification")
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": MOCK_KEY}):
        for case in cases:
            client = MockHttpClient(_make_mock_response("UNVERIFIABLE"))
            evidence = [evidence_by_id[eid] for eid in case["evidence_ids"]]
            actual = "REQUEST FAILED"
            try:
                card = claimcheck.check_claim(case["text"], evidence=evidence, client=client)
                actual = card["verdict"]
                if actual not in case["allowed_outcomes"] or client.call_count != 1:
                    raise AssertionError("Candidate abstention or one-call contract failed.")
                passed += 1
                status = "PASS (abstention policy)"
            except Exception:
                failures.append(f"{case['id']}: candidate abstention check failed")
                status = "FAIL"
            calls += client.call_count
            print(f"  [{case['id']}] review=PENDING; intended={case['expected_verdict']}; "
                  f"allowed=UNVERIFIABLE; actual={actual}; {status}")
            if verbose:
                print(f"    Candidate IDs: {case['evidence_ids']}; mock attempts={client.call_count}")
        print(f"Unreviewed candidate safety checks: {passed}/{len(cases)}")
        print(f"Candidate mock request attempts: {calls}; real requests: 0")
        print("Reviewed factual coverage: BLOCKED — no independent owner review receipts.")
        vp, vt, vf = run_validation_tests(verbose)
    failures.extend(vf)
    return passed + vp, len(cases) + vt, failures


def run_validation_tests(verbose: bool = False) -> tuple[int, int, list[str]]:
    """Invented reviewed receipts below are synthetic, never human review."""
    passed, total, calls = 0, 0, 0
    failures: list[str] = []
    claim = "Synthetic test sample has the approved property."
    evidence = [{"id": "synthetic-source", "publisher": "Synthetic test publisher",
                 "title": "Invented software fixture", "url": "https://example.invalid/fixture",
                 "date": "2026-10-23", "excerpt": claim, "verified_by_human": False}]
    receipt = {"schema": "claim-review/v1", "claim": claim, "verdict": "TRUE",
               "evidence_ids": ["synthetic-source"],
               "evidence_sha256": claimcheck.evidence_digest(evidence),
               "reviewed_by": "SYNTHETIC TEST ONLY — no actual reviewer", "reviewed_on": "2026-10-23"}

    def test(name: str, response: dict[str, Any] | None = None,
             error: Exception | None = None, expected_error: type | None = None,
             supplied: Any = None, review: Any = None, text: Any = claim,
             expected_calls: int = 1, expected_verdict: str = "UNVERIFIABLE") -> None:
        nonlocal passed, total, calls
        total += 1
        client = MockHttpClient(response, error)
        caught = None
        actual = None
        try:
            actual = claimcheck.check_claim(text, evidence=supplied, client=client, review=review)["verdict"]
        except Exception as exc:
            caught = type(exc)
        calls += client.call_count
        correct_error = (caught is None and actual == expected_verdict) if expected_error is None else (
            caught is not None and issubclass(caught, expected_error))
        if correct_error and client.call_count == expected_calls:
            passed += 1
            print(f"  [synthetic/{name}] PASS")
        else:
            failures.append(f"synthetic/{name}: exception or request-count mismatch")
            print(f"  [synthetic/{name}] FAIL")

    print("SYNTHETIC CONTRACT TESTS — invented receipts, no human source review")
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": MOCK_KEY}):
        for status in (401, 402, 429, 500):
            test(f"HTTP {status}", error=claimcheck.ProviderHTTPError(status, "synthetic"),
                 expected_error=claimcheck.ProviderHTTPError)
        test("timeout", error=claimcheck.ProviderTimeoutError("synthetic"),
             expected_error=claimcheck.ProviderTimeoutError)
        test("unreachable", error=claimcheck.ProviderUnreachableError("synthetic"),
             expected_error=claimcheck.ProviderUnreachableError)
        bad = _make_mock_response("UNVERIFIABLE")
        bad["choices"][0]["message"]["content"] = "{"
        test("malformed JSON", response=bad, expected_error=claimcheck.MalformedResponseError)
        for name, metadata in (("wrong model", "other/model:free"),
                               ("base-only model", claimcheck.FIXED_MODEL.removesuffix(":free")),
                               ("missing model", None)):
            bad = _make_mock_response("UNVERIFIABLE")
            if metadata is None:
                del bad["model"]
            else:
                bad["model"] = metadata
            test(name, response=bad, expected_error=claimcheck.ModelMismatchError)
        bad = _make_mock_response("UNVERIFIABLE")
        bad["choices"][0]["finish_reason"] = "length"
        test("truncated response", response=bad, expected_error=claimcheck.ClaimCheckError)
        test("unknown citation", response=_make_mock_response("UNVERIFIABLE", evidence_ids=["unknown"]),
             expected_error=claimcheck.ResponseValidationError)
        test("confident without evidence", response=_make_mock_response("TRUE"),
             expected_error=claimcheck.ResponseValidationError)
        test("confident unreviewed source", response=_make_mock_response("TRUE", evidence_ids=["synthetic-source"]),
             supplied=evidence, expected_error=claimcheck.ResponseValidationError)
        for verdict in ("TRUE", "FALSE", "MISLEADING"):
            test(f"reviewed {verdict}", response=_make_mock_response(verdict, evidence_ids=["synthetic-source"]),
                 supplied=evidence, review=dict(receipt, verdict=verdict), expected_verdict=verdict)
        test("reviewed source may abstain", response=_make_mock_response("UNVERIFIABLE"),
             supplied=evidence, review=receipt)
        test("opposite review verdict", response=_make_mock_response("FALSE", evidence_ids=["synthetic-source"]),
             supplied=evidence, review=receipt, expected_error=claimcheck.ResponseValidationError)
        test("stale receipt", response=_make_mock_response("UNVERIFIABLE"), supplied=evidence,
             review=dict(receipt, evidence_sha256="0" * 64),
             expected_error=claimcheck.InputValidationError, expected_calls=0)
        test("invalid evidence", response=_make_mock_response("UNVERIFIABLE"), supplied=[{"id": "missing-metadata"}],
             expected_error=claimcheck.InputValidationError, expected_calls=0)
        for name, text in (("blank claim", "  "), ("long claim", "x" * 2001), ("null claim", None)):
            test(name, response=_make_mock_response("UNVERIFIABLE"), text=text,
                 expected_error=claimcheck.InputValidationError, expected_calls=0)
        with patch.dict(os.environ, {}, clear=True):
            test("missing key", response=_make_mock_response("UNVERIFIABLE"),
                 expected_error=claimcheck.ConfigurationError, expected_calls=0)
    print(f"Synthetic contract checks: {passed}/{total}")
    print(f"Synthetic mock request attempts: {calls}; real requests: 0")
    return passed, total, failures


def load_case_reviews(
    cases: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]],
    review_dir: str | Path | None,
) -> dict[str, dict[str, Any]]:
    """Prevalidate every supplied receipt before the first live attempt."""
    if review_dir is None:
        return {}
    directory = Path(review_dir)
    try:
        if not directory.is_dir():
            raise EvalFixtureError("Review directory is unavailable.")
        files = [path for path in directory.iterdir() if path.suffix == ".json"]
    except OSError as exc:
        raise EvalFixtureError("Review directory is unavailable.") from exc
    by_filename = {f"{case['id']}.json": case for case in cases}
    if len(files) > len(cases) or any(path.name not in by_filename for path in files):
        raise EvalFixtureError("Unknown or excessive review receipts.")
    reviews = {}
    for path in files:
        case = by_filename[path.name]
        evidence = [evidence_by_id[eid] for eid in case["evidence_ids"]]
        try:
            receipt = claimcheck.load_review_file(str(path))
            # Share core binding validation; check_claim repeats it at use time.
            verdict, _ = claimcheck._validate_review(receipt, case["text"], evidence)
        except claimcheck.ClaimCheckError as exc:
            raise EvalFixtureError("Review receipt failed validation.") from exc
        if verdict != case["expected_verdict"]:
            raise EvalFixtureError("Review verdict differs from the intended case category.")
        reviews[case["id"]] = receipt
    return reviews


def run_live_tests(verbose: bool = False, confirm_free_allowance: bool = False,
                   client: Any = None, review_dir: str | Path | None = None) -> tuple[int, int, list[str]]:
    """Opt-in requests require separately confirmed available zero-cost allowance."""
    if not confirm_free_allowance:
        print("BLOCKED: live evaluation requires --confirm-free-allowance.")
        return 0, 0, ["BLOCKED: free allowance not confirmed"]
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key or key == MOCK_KEY:
        print("BLOCKED: live evaluation requires a locally configured real API key.")
        return 0, 0, ["BLOCKED: live key unavailable"]
    cases, evidence_by_id = load_cases()
    try:
        reviews = load_case_reviews(cases, evidence_by_id, review_dir)
    except EvalFixtureError:
        print("BLOCKED: invalid review receipts; no live requests attempted.")
        return 0, 0, ["BLOCKED: invalid review receipts"]
    counted = CountingHttpClient(client if client is not None else claimcheck.RealHttpClient(),
                                 min(len(cases), MAX_LIVE_CASES))
    passed, total = 0, 0
    failures: list[str] = []
    observed = {verdict: 0 for verdict in sorted(claimcheck.VALID_VERDICTS)}
    categories = sorted({receipt["verdict"] for receipt in reviews.values()})
    print(f"LIVE CANDIDATE EVALUATION — request cap {counted.limit}")
    print(f"Configured model: {claimcheck.FIXED_MODEL}")
    print(f"Receipt-reviewed candidates: {len(reviews)}/{len(cases)}; approved categories: {categories}")
    print("Missing receipts leave candidates PENDING; only UNVERIFIABLE is then allowed.")
    print("Abstention results do not verify TRUE/FALSE/MISLEADING factual coverage.")
    for case in cases:
        total += 1
        evidence = [evidence_by_id[eid] for eid in case["evidence_ids"]]
        review = reviews.get(case["id"])
        allowed = {"UNVERIFIABLE"}
        if review is not None:
            allowed.add(review["verdict"])
        review_status = "OWNER RECEIPT" if review is not None else "PENDING"
        try:
            card = claimcheck.check_claim(case["text"], evidence=evidence, client=counted, review=review)
            actual = card["verdict"]
            if actual in allowed:
                passed += 1
                status = "PASS (allowed outcome)"
            else:
                failures.append(f"{case['id']}: disallowed candidate outcome")
                status = "FAIL"
            observed[actual] += 1
            print(f"  [{case['id']}] review={review_status}; intended={case['expected_verdict']}; "
                  f"allowed={','.join(sorted(allowed))}; actual={actual}; {status}")
            if verbose:
                print(f"    Observed model: {card['model']}; cited IDs: {card['evidence_ids']}")
        except Exception:
            failures.append(f"{case['id']}: REQUEST FAILED")
            print(f"  [{case['id']}] REQUEST FAILED; stopping live run without retry.")
            break
    print(f"Live candidate checks: {passed}/{total}; declared cases: {len(cases)}")
    print(f"Observed verdict counts: {observed}")
    print(f"Live request attempts: {counted.call_count}; cap: {counted.limit}")
    return passed, total, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Opt in to hosted Gemma candidate checks.")
    parser.add_argument("--confirm-free-allowance", action="store_true",
                        help="Confirm available allowance for the zero-cost route before --live.")
    parser.add_argument("--review-dir", type=Path,
                        help="Optional directory of independently supplied case-ID.json receipts.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if (args.confirm_free_allowance or args.review_dir is not None) and not args.live:
        parser.error("--confirm-free-allowance and --review-dir require --live")
    try:
        passed, total, failures = run_mock_tests(args.verbose)
        print(f"\nOffline software checks: {passed}/{total}; real requests: 0")
        if failures:
            print("Offline checks FAILED. Live evaluation not started.")
            return 1
        if args.live:
            _, _, failures = run_live_tests(args.verbose, args.confirm_free_allowance, review_dir=args.review_dir)
            return 1 if failures else 0
    except EvalFixtureError:
        print("REQUEST FAILED: evaluation fixtures are invalid; no live requests started.")
        return 1
    print("Live Gemma execution: NOT RUN. Candidate human review: PENDING.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
