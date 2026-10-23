"""Offline routing and validation tests for Google-hosted free Gemma.

No network, no provider billing. A mock response tests only schema contracts.
"""
import json
import os
import unittest
from unittest.mock import patch

import claimcheck


def google_reply(model="gemma-4-26b-a4b-it", verdict="UNVERIFIABLE", evidence_ids=None):
    return {
        "modelVersion": model,
        "candidates": [{
            "content": {"parts": [{"text": json.dumps({
                "verdict": verdict,
                "rationale": "No reviewed source was provided.",
                "what_would_settle_it": "An independently reviewed primary source.",
                "evidence_ids": [] if evidence_ids is None else evidence_ids,
            })}]}
        }],
    }


class CaptureClient:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def post_json(self, url, headers, body, timeout):
        self.calls.append((url, headers, body, timeout))
        return self.result


class ProviderRoutingTests(unittest.TestCase):
    def test_allowlists_reject_paid_models_and_unknown_providers(self):
        for provider, model in [
            ("openrouter", "google/gemma-4-26b-a4b-it"),
            ("openrouter", "openrouter/free"),
            ("openrouter", "openai/gpt-4"),
            ("google", "gemini-3.8-flash"),
            ("google", "google/gemma-4-31b-it:free"),
            ("something-else", None),
        ]:
            with self.subTest(provider=provider, model=model):
                with self.assertRaises(claimcheck.ConfigurationError):
                    claimcheck.select_route(provider, model)

    def test_approved_routes_explicit_only(self):
        expected = (
            ("openrouter", "google/gemma-4-26b-a4b-it:free"),
            ("openrouter", "google/gemma-4-31b-it:free"),
            ("google", "gemma-4-26b-a4b-it"),
            ("google", "gemma-4-31b-it"),
        )
        for provider, model in expected:
            with self.subTest(provider=provider, model=model):
                chosen, url, key_name = claimcheck.select_route(provider, model)
                self.assertEqual(chosen, model)
                self.assertTrue(url.startswith("https://"))
                self.assertIn(key_name, ("OPENROUTER_API_KEY", "GEMINI_API_KEY"))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "offline-test-only"}, clear=True)
    def test_google_native_single_request_no_evidence_abstains(self):
        mock = CaptureClient(google_reply())
        card = claimcheck.check_claim("A test claim", client=mock, provider="google")
        self.assertEqual(card["verdict"], "UNVERIFIABLE")
        self.assertEqual(card["provider"], "google")
        self.assertEqual(card["model"], "gemma-4-26b-a4b-it")
        self.assertEqual(len(mock.calls), 1)
        url, headers, body, timeout = mock.calls[0]
        self.assertEqual(url, claimcheck.GOOGLE_API_URLS["gemma-4-26b-a4b-it"])
        self.assertNotIn("Authorization", headers)
        self.assertEqual(headers["x-goog-api-key"], "offline-test-only")
        self.assertNotIn("model", body)
        self.assertEqual(timeout, claimcheck.TIMEOUT_SECONDS)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "offline-test-only"}, clear=True)
    def test_google_31b_is_manual_and_exact(self):
        mock = CaptureClient(google_reply(model="gemma-4-31b-it"))
        card = claimcheck.check_claim(
            "A test claim", client=mock, provider="google", model="gemma-4-31b-it"
        )
        self.assertEqual(card["model"], "gemma-4-31b-it")
        self.assertEqual(len(mock.calls), 1)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "offline-test-only"}, clear=True)
    def test_google_missing_or_wrong_model_attestation_fails_closed(self):
        for reply in (google_reply(model=None), google_reply(model="gemma-4-31b-it"),
                      {"candidates": []}):
            with self.subTest(reply=reply.get("modelVersion")):
                mock = CaptureClient(reply)
                with self.assertRaises(claimcheck.ModelMismatchError):
                    claimcheck.check_claim("A test claim", client=mock, provider="google")
                self.assertEqual(len(mock.calls), 1)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "offline-test-only"}, clear=True)
    def test_google_confident_without_reviewed_sources_is_rejected(self):
        mock = CaptureClient(google_reply(verdict="TRUE"))
        with self.assertRaises(claimcheck.ResponseValidationError):
            claimcheck.check_claim("A test claim", client=mock, provider="google")

    def test_invalid_model_causes_zero_calls_even_with_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "offline-test-only"}, clear=True):
            mock = CaptureClient(google_reply())
            with self.assertRaises(claimcheck.ConfigurationError):
                claimcheck.check_claim(
                    "A test claim", client=mock, provider="google", model="gemini-3.8-flash"
                )
            self.assertEqual(mock.calls, [])

    def test_missing_google_key_causes_zero_calls(self):
        with patch.dict(os.environ, {}, clear=True):
            mock = CaptureClient(google_reply())
            with self.assertRaises(claimcheck.ConfigurationError):
                claimcheck.check_claim("A test claim", client=mock, provider="google")
            self.assertEqual(mock.calls, [])


if __name__ == "__main__":
    unittest.main()
