#!/usr/bin/env python3
"""
Evaluation runner for claim-checker-local.

Default mode:  Fully offline mock-HTTP evaluation using deterministic
               fixture responses.  No network, no API key required.

--live mode:   Opt-in real Gemma evaluation against the free endpoint.
               Requires OPENROUTER_API_KEY.  Hard-capped at 8 cases.
               Reports actual per-case results, not pre-determined passes.

Usage:
    python evals/run_eval.py              # mock-only (default)
    python evals/run_eval.py --live       # opt-in live Gemma test
    python evals/run_eval.py --live -v    # live with verbose output
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add parent directory to path for claimcheck import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import claimcheck

# ── Constants ────────────────────────────────────────────────────────
MAX_LIVE_CASES = 8
EVALS_DIR = Path(__file__).resolve().parent
CLAIMS_FILE = EVALS_DIR / "claims.json"
EVIDENCE_FILE = EVALS_DIR / "evidence.json"


# ── Mock HTTP client ─────────────────────────────────────────────────
class MockHttpClient:
    """Deterministic mock HTTP client for offline testing.

    Returns pre-configured responses keyed by claim text.
    Tracks call count.
    """

    def __init__(self, responses: dict[str, dict[str, Any]]):
        self.responses = responses
        self.call_count = 0
        self.last_request: dict[str, Any] | None = None

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        self.call_count += 1
        self.last_request = {"url": url, "headers": headers, "body": body}

        # Validate request structure
        assert url == claimcheck.OPENROUTER_URL, f"Wrong URL: {url}"
        assert body.get("model") == claimcheck.FIXED_MODEL, f"Wrong model: {body.get('model')}"
        assert "Authorization" in headers, "Missing Authorization header"

        # Extract claim from messages
        messages = body.get("messages", [])
        user_msg = ""
        for m in messages:
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        # Find matching response
        for claim_key, response in self.responses.items():
            if claim_key in user_msg:
                return response

        # Default: return UNVERIFIABLE for unknown claims
        return _make_mock_response("UNVERIFIABLE", "No matching mock found.", "Provide evidence.", [])


def _make_mock_response(
    verdict: str,
    rationale: str,
    what_would_settle_it: str,
    evidence_ids: list[str],
) -> dict[str, Any]:
    """Build a mock provider response matching the OpenRouter schema."""
    card = {
        "verdict": verdict,
        "rationale": rationale,
        "what_would_settle_it": what_would_settle_it,
        "evidence_ids": evidence_ids,
    }
    return {
        "model": claimcheck.FIXED_MODEL,
        "choices": [
            {
                "message": {
                    "content": json.dumps(card),
                    "role": "assistant",
                }
            }
        ],
    }


# ── Mock responses for each case ────────────────────────────────────
MOCK_RESPONSES: dict[str, dict[str, Any]] = {
    "Earth is the third planet from the Sun": _make_mock_response(
        "TRUE",
        "NASA's Earth Fact Sheet confirms Earth is the third planet from the Sun at a mean distance of 149.6 million km.",
        "Consult NASA planetary fact sheets or IAU records.",
        ["source-01"],
    ),
    "Pluto is classified as a full planet": _make_mock_response(
        "FALSE",
        "The IAU Resolution 5A (2006) reclassified Pluto as a 'dwarf planet', not a full planet.",
        "See IAU 2006 General Assembly Resolution 5A.",
        ["source-02"],
    ),
    "Neil Armstrong was the first person to walk on the Moon": _make_mock_response(
        "TRUE",
        "The Smithsonian Apollo 11 overview confirms Armstrong and Aldrin landed on the Moon on July 20, 1969.",
        "Consult NASA Apollo mission archives or Smithsonian records.",
        ["source-03"],
    ),
    "Great Wall of China is easily visible from space": _make_mock_response(
        "FALSE",
        "Encyclopaedia Britannica and astronaut reports confirm the Great Wall is not easily visible from space with the naked eye.",
        "Consult astronaut testimonies or space agency reports on Earth observation.",
        ["source-04"],
    ),
    "WHO reported 6 billion people used safely managed drinking-water services in 2022": _make_mock_response(
        "MISLEADING",
        "WHO gives this figure but also reports 2.2 billion without safely managed services. The nearly-everyone inference obscures that gap.",
        "See WHO/UNICEF data and define the intended meaning of nearly everyone.",
        ["source-05"],
    ),
    "The ocean contains most of Earth's water": _make_mock_response(
        "TRUE",
        "NOAA states the oceans contain about 97% of Earth's water. The literal claim is supported.",
        "Consult NOAA or USGS measurements for water distribution.",
        ["source-06"],
    ),
    "Bananas cure cancer": _make_mock_response(
        "UNVERIFIABLE",
        "No evidence was supplied to evaluate this medical claim. Model knowledge alone cannot verify medical claims.",
        "Peer-reviewed clinical studies from recognized medical journals.",
        [],
    ),
    "deep-sea fish was discovered in the Mariana Trench in 2025": _make_mock_response(
        "UNVERIFIABLE",
        "No evidence was supplied to evaluate this claim about a specific recent event.",
        "Published research or news reports with verifiable dates and institutional sources.",
        [],
    ),
}


# ── Error mock responses ────────────────────────────────────────────
class MockHttpError(MockHttpClient):
    """Mock that raises a provider HTTP error."""

    def __init__(self, status_code: int):
        super().__init__({})
        self.status_code = status_code

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        raise claimcheck.ProviderHTTPError(self.status_code, "mock error")


class MockHttpTimeout(MockHttpClient):
    """Mock that raises a timeout error."""

    def __init__(self):
        super().__init__({})

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        raise claimcheck.ProviderTimeoutError()


class MockHttpUnreachable(MockHttpClient):
    """Mock that raises an unreachable error."""

    def __init__(self):
        super().__init__({})

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        raise claimcheck.ProviderUnreachableError("mock DNS failure")


class MockHttpMalformed(MockHttpClient):
    """Mock that returns malformed JSON content."""

    def __init__(self):
        super().__init__({})

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        return {
            "model": claimcheck.FIXED_MODEL,
            "choices": [{"message": {"content": "not json at all {{{", "role": "assistant"}}],
        }


class MockHttpWrongModel(MockHttpClient):
    """Mock that returns a different model tag."""

    def __init__(self):
        super().__init__({})

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        return {
            "model": "openai/gpt-4",
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "verdict": "TRUE",
                            "rationale": "test",
                            "what_would_settle_it": "test",
                            "evidence_ids": [],
                        }),
                        "role": "assistant",
                    }
                }
            ],
        }


class MockHttpBadSchema(MockHttpClient):
    """Mock that returns valid JSON but missing required fields."""

    def __init__(self):
        super().__init__({})

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        return {
            "model": claimcheck.FIXED_MODEL,
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"verdict": "TRUE"}),
                        "role": "assistant",
                    }
                }
            ],
        }


class MockHttpFabricatedSource(MockHttpClient):
    """Mock that returns a verdict citing a non-existent evidence ID."""

    def __init__(self):
        super().__init__({})

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        return {
            "model": claimcheck.FIXED_MODEL,
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "verdict": "TRUE",
                            "rationale": "confirmed",
                            "what_would_settle_it": "nothing",
                            "evidence_ids": ["source-99-does-not-exist"],
                        }),
                        "role": "assistant",
                    }
                }
            ],
        }


class MockHttpConfidentNoEvidence(MockHttpClient):
    """Mock that returns TRUE without any evidence having been supplied."""

    def __init__(self):
        super().__init__({})

    def post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
        self.call_count += 1
        return {
            "model": claimcheck.FIXED_MODEL,
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "verdict": "TRUE",
                            "rationale": "I know this from training data.",
                            "what_would_settle_it": "nothing needed",
                            "evidence_ids": [],
                        }),
                        "role": "assistant",
                    }
                }
            ],
        }


# ── Test functions ───────────────────────────────────────────────────
def load_cases() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load claims and evidence from the evals fixtures."""
    with open(CLAIMS_FILE, encoding="utf-8") as f:
        claims_data = json.load(f)
    with open(EVIDENCE_FILE, encoding="utf-8") as f:
        evidence_data = json.load(f)

    cases = claims_data["cases"]
    evidence_by_id = {e["id"]: e for e in evidence_data["evidence"]}
    return cases, evidence_by_id


def run_mock_tests(verbose: bool = False) -> tuple[int, int, list[str]]:
    """Run all mock tests. Returns (passed, total, failure_messages)."""
    cases, evidence_by_id = load_cases()
    mock_client = MockHttpClient(MOCK_RESPONSES)

    passed = 0
    total = 0
    failures: list[str] = []

    # Set a fake API key for mock tests
    original_key = os.environ.get("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_API_KEY"] = "mock-test-key-not-real"

    try:
        print("=" * 60)
        print("MOCK EVALUATION (offline, deterministic)")
        print("=" * 60)

        for case in cases:
            total += 1
            case_id = case["id"]
            claim_text = case["text"]
            expected = case["expected_verdict"]
            allow_abstain = case.get("allow_abstain", False)
            case_evidence_ids = case.get("evidence_ids", [])

            # Gather evidence for this case
            evidence = [evidence_by_id[eid] for eid in case_evidence_ids if eid in evidence_by_id]

            try:
                unreviewed = bool(evidence) and not all(
                    e.get("verified_by_human") is True for e in evidence
                )
                if unreviewed:
                    # Test the refusal, not the truth of an unreviewed oracle.
                    try:
                        claimcheck.check_claim(
                            claim_text, evidence=evidence, client=mock_client
                        )
                    except claimcheck.ResponseValidationError:
                        passed += 1
                        print(f"  [{case_id}] PASS (confident verdict blocked: unreviewed source)")
                        continue
                    raise AssertionError("Confident verdict accepted with unreviewed source")

                card = claimcheck.check_claim(
                    claim_text,
                    evidence=evidence if evidence else None,
                    client=mock_client,
                )
                actual_verdict = card["verdict"]

                # Check result
                match = actual_verdict == expected
                abstained = actual_verdict == "UNVERIFIABLE" and allow_abstain

                if match or abstained:
                    passed += 1
                    status = "PASS"
                    if abstained and not match:
                        status = "PASS (abstained)"
                else:
                    status = "FAIL"
                    failures.append(
                        f"{case_id}: expected={expected}, got={actual_verdict}"
                    )

                if verbose:
                    print(f"\n  [{case_id}] {claim_text[:60]}...")
                    print(f"    Expected: {expected} | Got: {actual_verdict} | {status}")
                    print(f"    Rationale: {card['rationale'][:80]}...")
                else:
                    print(f"  [{case_id}] {status}: expected={expected}, got={actual_verdict}")

            except Exception as exc:
                failures.append(f"{case_id}: exception — {exc}")
                print(f"  [{case_id}] ERROR: {exc}")
                total += 0  # already counted

        print(f"\nMock contract cases: {passed}/{total} passed (not factual accuracy)")
        print(f"Mock HTTP calls: {mock_client.call_count}")

        # Additional validation tests
        print("\n" + "-" * 60)
        print("MOCK VALIDATION TESTS (error handling)")
        print("-" * 60)
        validation_passed, validation_total, validation_failures = run_validation_tests(verbose)
        passed += validation_passed
        total += validation_total
        failures.extend(validation_failures)

    finally:
        # Restore original key
        if original_key is not None:
            os.environ["OPENROUTER_API_KEY"] = original_key
        else:
            del os.environ["OPENROUTER_API_KEY"]

    return passed, total, failures


def run_validation_tests(verbose: bool = False) -> tuple[int, int, list[str]]:
    """Run error-handling and validation mock tests."""
    passed = 0
    total = 0
    failures: list[str] = []

    os.environ["OPENROUTER_API_KEY"] = "mock-test-key-not-real"

    test_claim = "Test claim for validation."

    validation_cases: list[tuple[str, type, Any]] = [
        ("HTTP 401 (unauthorized)", claimcheck.ProviderHTTPError, MockHttpError(401)),
        ("HTTP 402 (payment required)", claimcheck.ProviderHTTPError, MockHttpError(402)),
        ("HTTP 429 (rate limited)", claimcheck.ProviderHTTPError, MockHttpError(429)),
        ("HTTP 500 (server error)", claimcheck.ProviderHTTPError, MockHttpError(500)),
        ("Timeout", claimcheck.ProviderTimeoutError, MockHttpTimeout()),
        ("Unreachable", claimcheck.ProviderUnreachableError, MockHttpUnreachable()),
        ("Malformed JSON", claimcheck.MalformedResponseError, MockHttpMalformed()),
        ("Wrong model", claimcheck.ModelMismatchError, MockHttpWrongModel()),
        ("Missing fields", claimcheck.ResponseValidationError, MockHttpBadSchema()),
        ("Fabricated source ID", claimcheck.ResponseValidationError, MockHttpFabricatedSource()),
        ("Confident verdict without evidence", claimcheck.ResponseValidationError, MockHttpConfidentNoEvidence()),
    ]

    for name, expected_exc, mock_client in validation_cases:
        total += 1
        try:
            claimcheck.check_claim(test_claim, evidence=None, client=mock_client)
            # Should have raised
            failures.append(f"validation/{name}: expected {expected_exc.__name__} but no exception")
            print(f"  [validation/{name}] FAIL: no exception raised")
        except expected_exc:
            passed += 1
            print(f"  [validation/{name}] PASS")
        except Exception as exc:
            failures.append(f"validation/{name}: expected {expected_exc.__name__}, got {type(exc).__name__}: {exc}")
            print(f"  [validation/{name}] FAIL: {type(exc).__name__}: {exc}")

    # Input validation tests
    input_cases: list[tuple[str, str | None]] = [
        ("blank claim", "   "),
        ("too-long claim", "x" * 2001),
        ("None claim", None),
    ]

    for name, claim_input in input_cases:
        total += 1
        try:
            claimcheck.validate_claim(claim_input)
            failures.append(f"input/{name}: expected InputValidationError but none raised")
            print(f"  [input/{name}] FAIL: no exception raised")
        except claimcheck.InputValidationError:
            passed += 1
            print(f"  [input/{name}] PASS")
        except Exception as exc:
            failures.append(f"input/{name}: unexpected {type(exc).__name__}: {exc}")
            print(f"  [input/{name}] FAIL: {type(exc).__name__}")

    # Missing API key test
    total += 1
    original_key = os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        claimcheck.check_claim("test", client=MockHttpClient({}))
        failures.append("config/no-api-key: expected ConfigurationError")
        print("  [config/no-api-key] FAIL: no exception raised")
    except claimcheck.ConfigurationError:
        passed += 1
        print("  [config/no-api-key] PASS")
    except Exception as exc:
        failures.append(f"config/no-api-key: unexpected {type(exc).__name__}")
        print(f"  [config/no-api-key] FAIL: {type(exc).__name__}")
    finally:
        if original_key is not None:
            os.environ["OPENROUTER_API_KEY"] = original_key

    print(f"\nValidation tests: {passed}/{total} passed")
    return passed, total, failures


def run_live_tests(verbose: bool = False) -> tuple[int, int, list[str]]:
    """Run live tests against the real Gemma endpoint.

    Requires OPENROUTER_API_KEY to be set.
    Hard-capped at MAX_LIVE_CASES.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("BLOCKED: OPENROUTER_API_KEY not set. Cannot run live tests.")
        return 0, 0, ["BLOCKED: no API key"]

    if api_key == "mock-test-key-not-real":
        print("BLOCKED: Detected mock key. Set a real OPENROUTER_API_KEY for live tests.")
        return 0, 0, ["BLOCKED: mock key detected"]

    cases, evidence_by_id = load_cases()
    if len(cases) > MAX_LIVE_CASES:
        print(f"WARNING: {len(cases)} cases but live cap is {MAX_LIVE_CASES}. Running first {MAX_LIVE_CASES}.")
        cases = cases[:MAX_LIVE_CASES]

    passed = 0
    total = 0
    failures: list[str] = []
    call_count = 0

    print("=" * 60)
    print(f"LIVE EVALUATION (real Gemma endpoint, max {MAX_LIVE_CASES} cases)")
    print(f"Model: {claimcheck.FIXED_MODEL}")
    print(f"Endpoint: {claimcheck.OPENROUTER_URL}")
    print("=" * 60)

    for case in cases:
        total += 1
        case_id = case["id"]
        claim_text = case["text"]
        expected = case["expected_verdict"]
        allow_abstain = case.get("allow_abstain", False)
        case_evidence_ids = case.get("evidence_ids", [])

        evidence = [evidence_by_id[eid] for eid in case_evidence_ids if eid in evidence_by_id]

        if not case.get("provenance_reviewed", False) or any(
            e.get("verified_by_human") is not True for e in evidence
        ):
            failures.append(f"{case_id}: BLOCKED (source/case review pending)")
            print(f"  [{case_id}] BLOCKED: source/case review pending; no API call")
            continue

        print(f"\n  [{case_id}] Sending: {claim_text[:60]}...")

        try:
            start = time.time()
            call_count += 1
            card = claimcheck.check_claim(
                claim_text,
                evidence=evidence if evidence else None,
                client=None,  # Use real client
            )
            elapsed = time.time() - start
            actual_verdict = card["verdict"]

            match = actual_verdict == expected
            abstained = actual_verdict == "UNVERIFIABLE" and allow_abstain

            if match or abstained:
                passed += 1
                status = "PASS"
                if abstained and not match:
                    status = "PASS (honest abstention)"
            else:
                status = "FAIL"
                failures.append(
                    f"{case_id}: expected={expected}, got={actual_verdict}"
                )

            print(f"    Expected: {expected} | Got: {actual_verdict} | {status}")
            print(f"    Time: {elapsed:.1f}s")
            if verbose:
                print(f"    Rationale: {card['rationale'][:100]}...")
                print(f"    Evidence cited: {card['evidence_ids']}")

        except claimcheck.ProviderHTTPError as exc:
            failures.append(f"{case_id}: HTTP {exc.status_code}")
            print(f"    REQUEST FAILED: HTTP {exc.status_code}")
            print("    Provider failure — stopping live tests; no retry or fallback.")
            break
        except claimcheck.ClaimCheckError:
            failures.append(f"{case_id}: request/validation failure; batch stopped")
            print("    REQUEST FAILED: request/validation failure; stopping live tests.")
            break
        except Exception:
            failures.append(f"{case_id}: unexpected failure; batch stopped")
            print("    REQUEST FAILED: unexpected failure; stopping live tests.")
            break

    print(f"\nLive verdict cases: {passed}/{total} passed (reviewed cases only)")
    print(f"Live API calls made: {call_count}")
    print(f"Model: {claimcheck.FIXED_MODEL}")
    return passed, total, failures


# ── Main ─────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run claim-checker-local evaluation suite.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live tests against real Gemma endpoint (requires OPENROUTER_API_KEY).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output per case.",
    )
    args = parser.parse_args()

    total_passed = 0
    total_cases = 0
    all_failures: list[str] = []

    # Always run mock tests first
    mock_passed, mock_total, mock_failures = run_mock_tests(args.verbose)
    total_passed += mock_passed
    total_cases += mock_total
    all_failures.extend(mock_failures)

    if args.live:
        print("\n")
        live_passed, live_total, live_failures = run_live_tests(args.verbose)
        total_passed += live_passed
        total_cases += live_total
        all_failures.extend(live_failures)
    else:
        print("\n(Live tests skipped. Use --live to test against real Gemma endpoint.)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total: {total_passed}/{total_cases} passed")

    if all_failures:
        print("\nFailures:")
        for f in all_failures:
            print(f"  ✗ {f}")
        return 1

    print("\nAll tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

