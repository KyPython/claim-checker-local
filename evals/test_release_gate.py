"""Offline tests of live-run stopping and truthful request accounting."""
import contextlib
import io
import os
import unittest
from unittest.mock import patch

import claimcheck
import run_eval
from test_release_contract import provider_reply


class ReleaseGateTests(unittest.TestCase):
    def cases(self, reviewed):
        return ([{
            'id': f'test-{i}', 'text': 'A public test claim',
            'expected_verdict': 'UNVERIFIABLE', 'evidence_ids': [],
            'provenance_reviewed': reviewed,
        } for i in range(2)], {})

    def run_batch(self, reviewed, error=None):
        output = io.StringIO()
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'offline-test-only'}), \
             patch.object(run_eval, 'load_cases', return_value=self.cases(reviewed)), \
             patch.object(claimcheck, 'check_claim', side_effect=error) as check, \
             contextlib.redirect_stdout(output):
            result = run_eval.run_live_tests()
        return output.getvalue(), check.call_count, result

    def test_blocked_cases_make_and_report_zero_calls(self):
        output, calls, result = self.run_batch(False)
        self.assertEqual(calls, 0)
        self.assertIn('Live API calls made: 0', output)
        self.assertEqual(len(result[2]), 2)

    def test_provider_and_identity_failures_stop_after_one_attempt(self):
        for error in [claimcheck.ProviderHTTPError(code) for code in (401,402,429,500)] + [
            claimcheck.ModelMismatchError('private diagnostic'),
            claimcheck.ProviderUnreachableError('private diagnostic'),
            claimcheck.ProviderTimeoutError('private diagnostic'),
        ]:
            with self.subTest(error=type(error).__name__):
                output, calls, result = self.run_batch(True, error)
                self.assertEqual(calls, 1)
                self.assertIn('Live API calls made: 1', output)
                self.assertNotIn('private diagnostic', output)
                self.assertTrue(result[2])

    def test_untrusted_evidence_ids_are_not_echoed(self):
        private = 'PRIVATE_UNTRUSTED_TEXT'
        with self.assertRaises(claimcheck.ResponseValidationError) as raised:
            claimcheck.validate_provider_response(
                provider_reply(evidence_ids=[private]), set())
        self.assertNotIn(private, str(raised.exception))
