"""Bounded transport and local JSON checks; all HTTP openers are mocked."""
import io
import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

import claimcheck


class TransportTests(TestCase):
    def post(self):
        return claimcheck.RealHttpClient().post_json(
            claimcheck.OPENROUTER_URL,
            {"Authorization": "Bearer synthetic-test-key"},
            {"model": claimcheck.FIXED_MODEL}, 30,
        )

    def test_redirect_refuses_to_forward_authorization(self):
        request = urllib.request.Request(claimcheck.OPENROUTER_URL, headers={"Authorization": "Bearer synthetic-test-key"}, data=b"{}")
        handler = claimcheck._NoRedirectHandler()
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                with self.assertRaises(claimcheck.ProviderHTTPError):
                    handler.redirect_request(request, None, code, "redirect", {}, "https://example.org/collect")

    def test_response_read_is_bounded_and_no_retry(self):
        opener = MagicMock()
        result = opener.open.return_value.__enter__.return_value
        result.read.return_value = b"x" * (claimcheck.MAX_RESPONSE_BYTES + 1)
        with patch("urllib.request.build_opener", return_value=opener):
            with self.assertRaises(claimcheck.MalformedResponseError):
                self.post()
        opener.open.assert_called_once()
        result.read.assert_called_once_with(claimcheck.MAX_RESPONSE_BYTES + 1)

    def test_outer_json_rejects_duplicates_constants_bad_utf8_and_nonobjects(self):
        for raw in (b'{"model":"a","model":"b"}', b'{"x":NaN}', b'\xff', b'[]', b'null'):
            with self.subTest(raw=raw):
                opener = MagicMock()
                opener.open.return_value.__enter__.return_value.read.return_value = raw
                with patch("urllib.request.build_opener", return_value=opener):
                    with self.assertRaises(claimcheck.MalformedResponseError):
                        self.post()
                opener.open.assert_called_once()

    def test_provider_http_failure_does_not_read_or_echo_body(self):
        payload = io.BytesIO(b"SENSITIVE_ERROR_BODY_SENTINEL")
        failure = urllib.error.HTTPError(claimcheck.OPENROUTER_URL, 401, "SENSITIVE_REASON_SENTINEL", {}, payload)
        opener = MagicMock()
        opener.open.side_effect = failure
        with patch("urllib.request.build_opener", return_value=opener):
            with self.assertRaises(claimcheck.ProviderHTTPError) as caught:
                self.post()
        self.assertEqual(caught.exception.status_code, 401)
        self.assertNotIn("SENSITIVE", str(caught.exception))
        opener.open.assert_called_once()

    def test_unreachable_reason_is_sanitized_and_never_retried(self):
        opener = MagicMock()
        opener.open.side_effect = urllib.error.URLError("SENSITIVE_UNREACHABLE_SENTINEL")
        with patch("urllib.request.build_opener", return_value=opener):
            with self.assertRaises(claimcheck.ProviderUnreachableError) as caught:
                self.post()
        self.assertNotIn("SENSITIVE", str(caught.exception))
        opener.open.assert_called_once()

    def test_alternate_destination_is_rejected_before_building_opener(self):
        with patch("urllib.request.build_opener") as build:
            with self.assertRaises(claimcheck.ConfigurationError):
                claimcheck.RealHttpClient().post_json("https://example.org", {}, {}, 30)
            build.assert_not_called()

    def test_evidence_file_schema_duplicate_keys_and_size(self):
        candidates = [b'{"schema":"wrong/v1","evidence":[]}', b'{"schema":"claim-evidence/v1","evidence":[],"evidence":[]}', b'\xff', b"x" * (claimcheck.MAX_FILE_BYTES + 1)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            for data in candidates:
                with self.subTest(size=len(data)):
                    path.write_bytes(data)
                    with self.assertRaises(claimcheck.InputValidationError):
                        claimcheck.load_evidence_file(str(path))

    def test_valid_empty_evidence_file_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps({"schema": "claim-evidence/v1", "evidence": []}))
            self.assertEqual(claimcheck.load_evidence_file(str(path)), [])
