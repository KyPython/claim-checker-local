#!/usr/bin/env python3
"""
claim-checker-local — AI-assisted claim triage CLI.

Sends a single claim to cloud-hosted open-weight Gemma using an explicit
free-only provider/model selection and returns a preliminary verdict card.  This is NOT a source-grounded
authoritative fact checker; it is an AI-generated preliminary assessment.

Default:    google/gemma-4-26b-a4b-it:free via OpenRouter
Optional:   another pinned free Gemma or Google Gemini API hosted Gemma
Providers:  explicitly selected; never automatically fail over

Concept provenance: KyPython/claim-checker (private, idea Oct 17 2026).
This is a distinct new implementation for the Oct 19–25 contest window.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from typing import Any, Protocol

# ── Constants ────────────────────────────────────────────────────────
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FIXED_MODEL = "google/gemma-4-26b-a4b-it:free"  # Default; retained for mock compatibility
OPENROUTER_MODELS = frozenset({
    FIXED_MODEL,
    "google/gemma-4-31b-it:free",
})
GOOGLE_MODELS = frozenset({
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
})
GOOGLE_API_URLS = {
    model: f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    for model in GOOGLE_MODELS
}
# Explicit Google mode only; no automatic provider switch, paid model or reroute.
MAX_CLAIM_LEN = 2_000
TIMEOUT_SECONDS = 30
VALID_VERDICTS = frozenset({"TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"})
MAX_FIELD_LEN = 2_000  # cap for rationale / what_would_settle_it

DISCLOSURE = (
    "AI-generated preliminary assessment. "
    "Claim text was sent to a remote inference provider. "
    "This is not an authoritative fact-check."
)

SYSTEM_PROMPT = textwrap.dedent("""\
You are a claim-triage assistant.  You receive a CLAIM and optionally
a set of EVIDENCE excerpts (each with an id).  Your job:

1. If NO evidence is supplied, or the evidence is insufficient,
   you MUST return verdict "UNVERIFIABLE".
2. If supplied evidence directly supports the claim, return "TRUE".
3. If supplied evidence directly contradicts the claim, return "FALSE".
4. If evidence supports part but omits material context, return "MISLEADING".
5. You MUST NOT cite evidence IDs that were not supplied.
6. You MUST NOT fabricate URLs, sources or references.

Respond with ONLY a JSON object (no markdown fencing):
{
  "verdict": "<TRUE|FALSE|MISLEADING|UNVERIFIABLE>",
  "rationale": "<brief explanation>",
  "what_would_settle_it": "<what authoritative source would resolve this>",
  "evidence_ids": [<list of evidence IDs you relied on, or empty>]
}
""")


# ── HTTP client protocol (injectable for testing) ────────────────────
class HttpClient(Protocol):
    """Minimal injectable HTTP client interface."""

    def post_json(
        self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> dict[str, Any]: ...


class RealHttpClient:
    """stdlib urllib-based HTTP client — one request, no retries."""

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers=headers, method="POST"
        )
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            code = exc.code
            # Read error body safely but do not expose secrets
            try:
                err_body = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                err_body = ""
            raise ProviderHTTPError(code, err_body) from exc
        except urllib.error.URLError as exc:
            # Network errors can contain user-controlled URLs or environment details.
            raise ProviderUnreachableError("Unable to reach inference provider.") from exc
        except TimeoutError as exc:
            raise ProviderTimeoutError() from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MalformedResponseError(f"Invalid JSON from provider: {exc}") from exc


# ── Custom exceptions ────────────────────────────────────────────────
class ClaimCheckError(Exception):
    """Base for all application-level errors."""


class InputValidationError(ClaimCheckError):
    """Bad user input (blank, too long, etc.)."""


class ConfigurationError(ClaimCheckError):
    """Missing or invalid configuration (e.g. no API key)."""


class ProviderHTTPError(ClaimCheckError):
    """Provider returned an HTTP error status."""

    def __init__(self, status_code: int, body: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Provider returned HTTP {status_code}")


class ProviderUnreachableError(ClaimCheckError):
    """Network / DNS failure reaching provider."""


class ProviderTimeoutError(ClaimCheckError):
    """Request timed out."""


class MalformedResponseError(ClaimCheckError):
    """Provider JSON was unparseable or structurally wrong."""


class ModelMismatchError(ClaimCheckError):
    """Provider reported a different model than expected."""


class ResponseValidationError(ClaimCheckError):
    """Parsed response failed schema/contract validation."""


# ── Input validation ─────────────────────────────────────────────────
def validate_claim(text: str | None) -> str:
    """Return trimmed claim or raise InputValidationError."""
    if text is None:
        raise InputValidationError("No claim provided.")
    text = text.strip()
    if not text:
        raise InputValidationError("Claim is blank after trimming.")
    if len(text) > MAX_CLAIM_LEN:
        raise InputValidationError(
            f"Claim exceeds {MAX_CLAIM_LEN} characters ({len(text)})."
        )
    return text


# ── Evidence loading ─────────────────────────────────────────────────
def load_evidence_file(path: str) -> list[dict[str, Any]]:
    """Load a JSON evidence file and return the evidence list.

    Expected schema: {"schema": "claim-evidence/v1", "evidence": [...]}
    Each evidence item must have at minimum: id, excerpt.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise InputValidationError(f"Cannot read evidence file: {exc}") from exc

    if not isinstance(data, dict) or "evidence" not in data:
        raise InputValidationError(
            "Evidence file must be a JSON object with an 'evidence' key."
        )

    evidence = data["evidence"]
    if not isinstance(evidence, list):
        raise InputValidationError("'evidence' must be a list.")

    for item in evidence:
        if not isinstance(item, dict):
            raise InputValidationError("Each evidence entry must be a JSON object.")
        if "id" not in item or "excerpt" not in item:
            raise InputValidationError(
                f"Evidence entry missing required 'id' or 'excerpt': {item.get('id', '?')}"
            )

    return evidence


# ── Prompt construction ──────────────────────────────────────────────
def build_user_message(claim: str, evidence: list[dict[str, Any]] | None) -> str:
    """Build the user message for the model.

    Claim and evidence are DATA, never interpreted as instructions.
    """
    parts = [f"CLAIM: {claim}"]
    if evidence:
        parts.append("\nEVIDENCE:")
        for item in evidence:
            parts.append(
                f"  [{item['id']}] {item.get('publisher', 'unknown')}: "
                f"{item['excerpt']}"
            )
    else:
        parts.append("\nNo evidence supplied.")
    return "\n".join(parts)


# ── Response validation ──────────────────────────────────────────────
def validate_provider_response(
    raw_response: dict[str, Any],
    supplied_evidence_ids: set[str],
    reviewed_evidence_ids: set[str] | None = None,
    expected_model: str = FIXED_MODEL,
) -> dict[str, Any]:
    """Extract and validate the verdict card from the provider response.

    Raises ResponseValidationError or ModelMismatchError.
    Returns the validated card dict.
    """
    if not isinstance(raw_response, dict):
        raise MalformedResponseError("Provider response is not a JSON object.")

    # Do not infer free-tier identity by stripping :free or trusting absent metadata.
    # Some providers might report an alias; fail closed until independently verified.
    returned_model = raw_response.get("model")
    if not _model_matches(returned_model, expected_model):
        raise ModelMismatchError(
            "Provider response did not attest the exact configured free Gemma model."
        )

    # Extract message content
    try:
        choices = raw_response["choices"]
        content = choices[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MalformedResponseError(
            f"Cannot extract message content from response: {exc}"
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise MalformedResponseError("Empty message content from provider.")

    # Parse the JSON verdict from model output
    # Strip markdown code fences if the model wraps them
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    try:
        card = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Never echo raw model output: it can contain private claim/evidence text.
        raise MalformedResponseError("Model output is not valid JSON.") from exc

    if not isinstance(card, dict):
        raise ResponseValidationError("Model output is not a JSON object.")

    # Required fields from model
    for field in ("verdict", "rationale", "what_would_settle_it", "evidence_ids"):
        if field not in card:
            raise ResponseValidationError(f"Missing required field: '{field}'")

    # Validate verdict enum
    verdict = card["verdict"]
    if not isinstance(verdict, str) or verdict.upper() not in VALID_VERDICTS:
        raise ResponseValidationError(
            "Invalid verdict. Expected a supported verdict enum."
        )
    card["verdict"] = verdict.upper()

    # Validate text field lengths
    for field in ("rationale", "what_would_settle_it"):
        val = card[field]
        if not isinstance(val, str) or not val.strip():
            raise ResponseValidationError(f"'{field}' must be a non-empty string.")
        if len(val) > MAX_FIELD_LEN:
            raise ResponseValidationError(
                f"'{field}' exceeds {MAX_FIELD_LEN} characters."
            )

    # Validate evidence_ids
    evidence_ids = card["evidence_ids"]
    if not isinstance(evidence_ids, list):
        raise ResponseValidationError("'evidence_ids' must be a list.")
    for eid in evidence_ids:
        if not isinstance(eid, str):
            raise ResponseValidationError(
                f"Evidence ID must be a string, got {type(eid).__name__}."
            )
        if eid not in supplied_evidence_ids:
            raise ResponseValidationError(
                "Model cited an evidence ID that was not supplied."
            )

    # Evidence IDs alone do not establish reviewed provenance or even that the model
    # cited the evidence. This is a safety gate, NOT semantic entailment verification.
    if card["verdict"] in ("TRUE", "FALSE", "MISLEADING"):
        reviewed = reviewed_evidence_ids or set()
        if not evidence_ids or not set(evidence_ids).issubset(reviewed):
            raise ResponseValidationError(
                "A confident verdict requires cited, explicitly reviewed evidence. "
                "Otherwise the model must abstain with UNVERIFIABLE."
            )

    return card


def _model_matches(returned: Any, expected: str = FIXED_MODEL) -> bool:
    """Require exact expected model identity; never strip :free or accept aliases."""
    return isinstance(returned, str) and returned == expected


def select_route(provider: str, model: str | None) -> tuple[str, str, str]:
    """Select an exact published free Gemma route before reading credentials."""
    if provider == "openrouter":
        chosen = model or FIXED_MODEL
        if chosen not in OPENROUTER_MODELS:
            raise ConfigurationError("Only explicitly approved free Gemma models are allowed.")
        return chosen, OPENROUTER_URL, "OPENROUTER_API_KEY"
    if provider == "google":
        chosen = model or "gemma-4-26b-a4b-it"
        if chosen not in GOOGLE_MODELS:
            raise ConfigurationError("Only Google-hosted free Gemma 4 models are allowed.")
        return chosen, GOOGLE_API_URLS[chosen], "GEMINI_API_KEY"
    raise ConfigurationError("Provider must be 'openrouter' or 'google'.")


def normalize_google_response(raw: dict[str, Any], expected_model: str) -> dict[str, Any]:
    """Require Google generateContent modelVersion before adapting to shared card gate."""
    if not isinstance(raw, dict):
        raise MalformedResponseError("Google provider response is not a JSON object.")
    if raw.get("modelVersion") != expected_model:
        raise ModelMismatchError("Google provider did not attest the exact selected Gemma model.")
    try:
        parts = raw["candidates"][0]["content"]["parts"]
        if len(parts) != 1 or not isinstance(parts[0]["text"], str):
            raise ValueError("Expected one text response part.")
        content = parts[0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise MalformedResponseError("Google response has no single usable text candidate.") from exc
    return {"model": expected_model, "choices": [{"message": {"content": content}}]}


# ── Core check function ─────────────────────────────────────────────
def check_claim(
    claim: str,
    evidence: list[dict[str, Any]] | None = None,
    client: HttpClient | None = None,
    provider: str = "openrouter",
    model: str | None = None,
) -> dict[str, Any]:
    """Run a single claim check. Returns the complete verdict card.

    Args:
        claim: Validated claim text.
        evidence: Optional list of evidence dicts with 'id' and 'excerpt'.
        client: Injectable HTTP client (defaults to RealHttpClient).

    Returns:
        Complete verdict card dict.

    Raises:
        ConfigurationError: Missing API key.
        ProviderHTTPError, ProviderUnreachableError, ProviderTimeoutError:
            Network/provider failures.
        MalformedResponseError, ResponseValidationError, ModelMismatchError:
            Response contract violations.
    """
    selected_model, endpoint_url, key_name = select_route(provider, model)
    api_key = os.environ.get(key_name, "").strip()
    if not api_key:
        raise ConfigurationError(f"{key_name} is not set. Provide the selected provider's key privately.")

    if client is None:
        client = RealHttpClient()

    supplied_ids: set[str] = set()
    reviewed_ids: set[str] = set()
    if evidence:
        supplied_ids = {e["id"] for e in evidence}
        reviewed_ids = {
            e["id"] for e in evidence
            if e.get("verified_by_human") is True
            and all(isinstance(e.get(k), str) and e[k].strip()
                    for k in ("id", "title", "publisher", "excerpt", "url"))
            and e["url"].startswith("https://")
        }
        # Flags are user declarations, not independent authentication of source
        # relevance, integrity, recency, or truth.

    user_msg = build_user_message(claim, evidence)

    if provider == "openrouter":
        request_body: dict[str, Any] = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0,
            "max_tokens": 700,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/KyPython/claim-checker-local",
            "X-Title": "claim-checker-local",
        }
    else:
        # Google native generateContent API, not unverified compatibility routing.
        request_body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 700},
        }
        headers = {"x-goog-api-key": api_key}

    raw_response = client.post_json(endpoint_url, headers, request_body, TIMEOUT_SECONDS)
    if provider == "google":
        raw_response = normalize_google_response(raw_response, selected_model)

    card = validate_provider_response(
        raw_response, supplied_ids, reviewed_ids, expected_model=selected_model
    )

    # Code-controlled fields (not model-asserted)
    card["claim"] = claim
    card["model"] = selected_model
    card["disclosure"] = DISCLOSURE
    card["provider"] = provider

    return card


# ── Output formatting ───────────────────────────────────────────────
def format_card_text(card: dict[str, Any]) -> str:
    """Format verdict card for human-readable terminal output."""
    lines = [
        "╔══════════════════════════════════════════════════╗",
        "║           CLAIM TRIAGE — VERDICT CARD            ║",
        "╚══════════════════════════════════════════════════╝",
        "",
        f"  Claim:    {_wrap_field(card['claim'], 42)}",
        f"  Verdict:  {card['verdict']}",
        f"  Model:    {card['model']}",
        "",
        f"  Rationale:",
        f"    {_wrap_field(card['rationale'], 48)}",
        "",
        f"  What would settle it:",
        f"    {_wrap_field(card['what_would_settle_it'], 48)}",
        "",
    ]

    if card.get("evidence_ids"):
        lines.append(f"  Evidence cited: {', '.join(card['evidence_ids'])}")
    else:
        lines.append("  Evidence cited: (none)")

    lines.extend([
        "",
        f"  ⚠ {card['disclosure']}",
        "",
    ])

    return "\n".join(lines)


def _wrap_field(text: str, width: int) -> str:
    """Wrap long text for display."""
    wrapped = textwrap.fill(text, width=width, subsequent_indent="            ")
    return wrapped


# ── CLI entry point ──────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claimcheck",
        description=(
            "AI-assisted claim triage using cloud-hosted Gemma. "
            "This is a preliminary assessment tool, not an authoritative fact-checker."
        ),
    )
    parser.add_argument(
        "--claim",
        type=str,
        default=None,
        help="The claim to evaluate (alternatively, pipe via stdin).",
    )
    parser.add_argument(
        "--evidence-file",
        type=str,
        default=None,
        help="Path to a JSON file with reviewed evidence excerpts.",
    )
    parser.add_argument(
        "--provider", choices=("openrouter", "google"), default="openrouter",
        help="Choose a provider explicitly; no automatic fallback (default: openrouter).",
    )
    parser.add_argument(
        "--model", default=None,
        help="Exact allowlisted free Gemma model ID for the selected provider.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output the verdict card as JSON instead of formatted text.",
    )
    return parser


def main(argv: list[str] | None = None, client: HttpClient | None = None) -> int:
    """CLI entry point. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Determine claim source: --claim takes precedence
    claim_text: str | None = args.claim
    if claim_text is None:
        if not sys.stdin.isatty():
            claim_text = sys.stdin.read()
        else:
            print("Error: No claim provided. Use --claim or pipe via stdin.", file=sys.stderr)
            return 1

    try:
        claim = validate_claim(claim_text)
    except InputValidationError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 1

    evidence: list[dict[str, Any]] | None = None
    if args.evidence_file:
        try:
            evidence = load_evidence_file(args.evidence_file)
        except InputValidationError as exc:
            print(f"Evidence error: {exc}", file=sys.stderr)
            return 1

    try:
        card = check_claim(
            claim, evidence=evidence, client=client, provider=args.provider, model=args.model
        )
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except ProviderHTTPError as exc:
        status = exc.status_code
        if status == 401:
            msg = "REQUEST FAILED: Unauthorized (401). Check the selected provider key."
        elif status == 402:
            msg = "REQUEST FAILED: Payment required (402). Free endpoint may not be available."
        elif status == 429:
            msg = "REQUEST FAILED: Rate limited (429). Free quota may be exhausted."
        elif status >= 500:
            msg = f"REQUEST FAILED: Provider server error ({status})."
        else:
            msg = f"REQUEST FAILED: HTTP {status} from provider."
        print(msg, file=sys.stderr)
        return 1
    except ProviderUnreachableError:
        print("REQUEST FAILED: Provider unreachable.", file=sys.stderr)
        return 1
    except ProviderTimeoutError:
        print(
            f"REQUEST FAILED: Request timed out after {TIMEOUT_SECONDS}s.",
            file=sys.stderr,
        )
        return 1
    except (MalformedResponseError, ResponseValidationError, ModelMismatchError) as exc:
        print(f"REQUEST FAILED: {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(card, indent=2, ensure_ascii=False))
    else:
        print(format_card_text(card))

    return 0


if __name__ == "__main__":
    sys.exit(main())