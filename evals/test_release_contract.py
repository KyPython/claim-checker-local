"""Release-contract regression tests: deterministic; NO network or billing.

These tests verify validation decisions, not source truth or live inference.
Run: python3 -m unittest discover -s evals -p 'test_*.py' -v
"""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import claimcheck


def provider_reply(verdict="UNVERIFIABLE", evidence_ids=None, model=claimcheck.FIXED_MODEL):
    card = {
        "verdict": verdict,
        "rationale": "An artificial test-only response.",
        "what_would_settle_it": "A reviewed primary source.",
        "evidence_ids": evidence_ids if evidence_ids is not None else [],
    }
    return {
        "model": model,
        "choices": [{"message": {"content": json.dumps(card)}}],
    }


class ReleaseContractTests(unittest.TestCase):
    def test_fixed_model_has_free_suffix(self):
        self.assertEqual(claimcheck.FIXED_MODEL, "google/gemma-4-26b-a4b-it:free")

    def test_missing_model_metadata_fails_closed(self):
        response = provider_reply()
        del response["model"]
        with self.assertRaises(claimcheck.ModelMismatchError):
            claimcheck.validate_provider_response(response, set())

    def test_paid_variant_without_free_suffix_fails_closed(self):
        with self.assertRaises(claimcheck.ModelMismatchError):
            claimcheck.validate_provider_response(
                provider_reply(model="google/gemma-4-26b-a4b-it"), set()
            )

    def test_wrong_provider_model_fails_closed(self):
        with self.assertRaises(claimcheck.ModelMismatchError):
            claimcheck.validate_provider_response(
                provider_reply(model="openai/gpt-4"), set()
            )

    def test_abstention_without_evidence_is_valid_contract(self):
        card = claimcheck.validate_provider_response(provider_reply(), set())
        self.assertEqual(card["verdict"], "UNVERIFIABLE")

    def test_confident_without_cited_evidence_is_rejected(self):
        with self.assertRaises(claimcheck.ResponseValidationError):
            claimcheck.validate_provider_response(
                provider_reply(verdict="TRUE"), {"e1"}, {"e1"}
            )

    def test_confident_cited_but_unreviewed_evidence_is_rejected(self):
        with self.assertRaises(claimcheck.ResponseValidationError):
            claimcheck.validate_provider_response(
                provider_reply(verdict="TRUE", evidence_ids=["e1"]), {"e1"}, set()
            )

    def test_unknown_evidence_id_is_rejected(self):
        with self.assertRaises(claimcheck.ResponseValidationError):
            claimcheck.validate_provider_response(
                provider_reply(verdict="TRUE", evidence_ids=["fabricated"]), {"e1"}, {"e1"}
            )

    def test_reviewed_flag_allows_schema_only_not_truth_proof(self):
        card = claimcheck.validate_provider_response(
            provider_reply(verdict="TRUE", evidence_ids=["e1"]), {"e1"}, {"e1"}
        )
        self.assertEqual(card["evidence_ids"], ["e1"])
        # Passing this contract test does NOT verify semantic entailment or human review.

    def test_invalid_json_does_not_echo_private_model_output(self):
        secret = "PRIVATE_UNTRUSTED_CLAIM_PAYLOAD_123"
        response = provider_reply()
        response["choices"][0]["message"]["content"] = secret + " {{"
        with self.assertRaises(claimcheck.MalformedResponseError) as raised:
            claimcheck.validate_provider_response(response, set())
        self.assertNotIn(secret, str(raised.exception))

    def test_no_unintended_paid_model_auto_router(self):
        self.assertNotEqual(claimcheck.FIXED_MODEL, "openrouter/free")
        self.assertTrue(claimcheck.OPENROUTER_URL.startswith("https://"))


if __name__ == "__main__":
    unittest.main()
