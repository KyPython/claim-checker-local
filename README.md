# claim-checker-local

A Python claim-triage CLI designed to send one claim to cloud-hosted open-weight **Gemma** through OpenRouter and return a provisional verdict card. The CLI runs locally; model inference is remote.

**Status — October 23, 2026:** local implementation and offline validation are documented in the [verification receipt](docs/verification-2026-10-23.md). **Live Gemma inference, independent evidence review, a recorded demo, human code review, and final submission approval remain pending. No DEV entry has been published by this completion run.** Mock results demonstrate software behavior, not factual accuracy or actual Gemma execution.

This project targets the [DEV Hacktoberfest Open-Source AI Challenge, Week 3 — Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19). Best Use of Gemma remains a conditional category until a real Gemma receipt exists.

## Run offline checks first

Requires **Python 3.11+**, with no third-party packages or local model installation.

```bash
git clone https://github.com/KyPython/claim-checker-local.git
cd claim-checker-local

# Deterministic evaluation; no key or network required.
python3 evals/run_eval.py

# Adversarial regression tests; no key or network required.
python3 -m unittest discover -s tests -v
```

The evaluation prints each candidate's review status, effective allowed outcomes, observed outcome, and request counts. The eight candidate cases cover four *intended* label categories, but every bundled fixture is unreviewed: **only `UNVERIFIABLE` is currently allowed**. Synthetic review receipts in tests exercise the approval boundary; they do not establish human review. Exact executed checks and results belong in the [verification receipt](docs/verification-2026-10-23.md).

## Run an actual claim

A live invocation requires an OpenRouter account, a process-environment `OPENROUTER_API_KEY`, and owner-confirmed free allowance for the exact endpoint. Configure the key locally without pasting it into chat, screenshots, or committed files. The CLI does not load `.env` files automatically.

After confirming access and allowance:

```bash
python3 claimcheck.py --claim "Earth is the third planet from the Sun."

printf '%s\n' 'An unsupported claim.' | python3 claimcheck.py --json

# Candidate evidence alone still permits only UNVERIFIABLE.
python3 claimcheck.py --claim "Earth is the third planet from the Sun." \
  --evidence-file evals/evidence.json
```

These commands make a real remote request; they are not offline examples. No successful output from them is claimed here. Without a key the CLI exits with a configuration error and makes zero requests. `--claim` takes precedence over stdin when both are supplied. Claims are trimmed, must be nonblank, and are limited to 2,000 characters.

The request uses the fixed URL `https://openrouter.ai/api/v1/chat/completions` and exact model `google/gemma-4-26b-a4b-it:free`. There is at most one inference request per valid claim, a 30-second timeout, zero-price provider limits, and no redirects, retries, or provider/model fallbacks. These controls do not prove current account allowance or successful zero-cost routing. The [public model listing](https://openrouter.ai/api/v1/models) and [routing controls](https://openrouter.ai/docs/guides/routing/provider-selection) are provider documentation, not a live execution receipt.

**Live metadata compatibility is untested.** The validator intentionally requires the full exact `:free` response tag under the completion specification. Missing or different provider metadata, including a base ID without `:free`, fails the request. If the provider reports only a base ID, resolving that needs a reviewed specification/provider decision; the app never silently relaxes the check. Matching metadata is a contract check, not cryptographic proof of model provenance.

## Evidence and the review boundary

Evidence is candidate data. Neither a source-looking URL nor `verified_by_human: true` in an evidence file authorizes a confident verdict. The app does not browse, verify source quotations, or independently establish entailment.

An evidence file uses `claim-evidence/v1` and an `evidence` list. Each entry needs a unique nonempty `id`, `publisher`, `title`, HTTPS `url`, ISO `date`, and bounded nonempty `excerpt`. See [evals/evidence.json](evals/evidence.json) for the candidate format; its excerpts, dates, and provenance still need independent review.

A confident label additionally requires a separately supplied **local owner review receipt**. After independently checking the exact claim, source provenance, excerpts, relevance, and any conflicting or missing context, the reviewer records one approved label and the supporting source IDs. The receipt schema is:

```json
{
  "schema": "claim-review/v1",
  "claim": "Earth is the third planet from the Sun.",
  "verdict": "TRUE",
  "evidence_ids": ["source-01"],
  "evidence_sha256": "REPLACE_WITH_DIGEST_ONLY_AFTER_INDEPENDENT_REVIEW",
  "reviewed_by": "REPLACE_WITH_ACTUAL_REVIEWER",
  "reviewed_on": "YYYY-MM-DD"
}
```

**This is an invalid, illustrative receipt, not evidence of a completed review. No real human-review receipt is bundled.** Compute the content digest for the *complete evidence list supplied to that invocation*, including metadata:

```bash
python3 -c 'from claimcheck import evidence_digest, load_evidence_file; print(evidence_digest(load_evidence_file("evals/evidence.json")))'
```

The helper hashes UTF-8 JSON after sorting the evidence list by ID, with sorted object keys, `ensure_ascii=False`, and compact separators. For the CLI command above, this is the whole `evals/evidence.json` evidence list. The evaluation runner selects a smaller list per case; its receipt workflow is described below. Changing any bound content requires a new independent review and receipt. A digest binds content; it does not authenticate reviewer identity. Supplying a receipt is an explicit local trust decision.

Only after that real review, save the completed receipt locally and pass it with the same evidence:

```bash
python3 claimcheck.py --claim "Earth is the third planet from the Sun." \
  --evidence-file evals/evidence.json --review-file /path/to/local-review.json
```

Malformed, mismatched, duplicate, empty-source, or stale-content receipts fail before inference. With a valid receipt, the model may abstain or return the approved label; a confident card must cite exactly the approved source IDs. A model answer cannot approve itself.

| Verdict | Provisional meaning with independently reviewed evidence |
|---|---|
| `TRUE` | Directly supports the material claim |
| `FALSE` | Directly contradicts the material claim |
| `MISLEADING` | Supports part of the claim, but missing context materially changes interpretation |
| `UNVERIFIABLE` | Evidence is absent, unreviewed, insufficient, conflicting, or otherwise inadequate |

## Opt-in live evaluation

The completion run made **no live inference calls**. The live runner requires both flags, the environment key, and confirmed free allowance:

```bash
python3 evals/run_eval.py --live --confirm-free-allowance
```

This sends at most eight requests, counts actual attempts, stops after provider failure, and never retries. Missing prerequisites produce `BLOCKED` with a nonzero exit. An abstention on an unreviewed candidate is not verified coverage of its intended TRUE/FALSE/MISLEADING category. Free-route availability and account limits may change; the flag is a human confirmation, not an account-balance check.

To evaluate independently reviewed candidates later, supply `--review-dir /path/to/local-reviews`. Save each real `claim-review/v1` receipt as its case ID plus `.json`, for example `case-01.json`. Its claim and approved verdict must match the candidate, and its digest must bind **exactly that case's supplied evidence subset**, not the whole corpus. The following offline helper shows the candidate fields and subset digest; it does not perform or attest to review:

```bash
python3 - <<'PY'
from claimcheck import evidence_digest
from evals.run_eval import load_cases

cases, sources = load_cases()
case = next(item for item in cases if item["id"] == "case-01")
evidence = [sources[source_id] for source_id in case["evidence_ids"]]
print("claim:", case["text"])
print("intended verdict:", case["expected_verdict"])
print("evidence_ids:", case["evidence_ids"])
print("evidence_sha256:", evidence_digest(evidence))
PY
```

Only after genuine independent review and confirmed live prerequisites:

```bash
python3 evals/run_eval.py --live --confirm-free-allowance \
  --review-dir /path/to/local-reviews
```

All supplied case receipts are validated before any live attempt. A valid receipt permits the approved intended label or honest abstention; a missing receipt leaves that case explicitly unreviewed and allows only `UNVERIFIABLE`. Cases without adequate sources must remain unreviewed. The runner reports reviewed coverage separately, so an all-abstention run is never presented as four-label accuracy. Do not change fixture review flags or create receipts merely to obtain a passing score.

## Output, failures, and privacy

A successful card contains exactly `claim`, `verdict`, `rationale`, `what_would_settle_it`, `model`, `evidence_ids`, and `disclosure`. The code controls the claim, model label, and disclosure. `--json` preserves literal text as JSON; human-readable output escapes terminal controls.

Transport and validation failures produce **REQUEST FAILED** with a nonzero exit, never a successful `UNVERIFIABLE` card. This includes HTTP 401/402/429/5xx, timeouts, unreachable providers, malformed or truncated responses, missing/wrong model metadata, unknown or duplicate citations, and unsupported confident labels. Errors use sanitized fixed messages. Input, evidence, review, and key validation failures make zero requests; exit 0 is reserved for a valid card.

Claim text and supplied excerpts travel to OpenRouter and its inference provider. Do not submit secrets, confidential information, or sensitive personal data. The CLI does not persist claims or keys, but cannot promise offline inference, end-to-end privacy, or no provider retention. Cards are AI-generated preliminary assessments, not authoritative fact-checks or medical, legal, or financial advice.

## Specification, demo, and submission

Implementation follows [issue #1 — SPEC v2](https://github.com/KyPython/claim-checker-local/issues/1), [requirements R01–R12](specs/claim-checker-local/requirements.md), the [design](specs/claim-checker-local/design.md), and the [completion requirements](specs/claim-checker-local/completion.md) written before these completion changes. The original requirements/design status lines describe their pre-implementation state; current execution status is in the [verification receipt](docs/verification-2026-10-23.md) and [tasks](specs/claim-checker-local/tasks.md).

- [A1–A12 local verification receipt](docs/verification-2026-10-23.md)
- [60–90-second real-run demo checklist](docs/demo.md) — recording pending
- [Unpublished DEV draft](docs/dev-submission-draft.md) — conspicuous live/demo placeholders remain

The [official challenge page](https://dev.to/challenges/hacktoberfest-week3-2026-10-19) requires one DEV post with `devchallenge`/`hf26challenge` tags and a video or deployed demo. The deadline is **October 25, 2026, 11:59 PM PDT** (October 26, 2:59 AM EDT). Before publication, the owner must confirm personal eligibility and the active form, review originality/code/evidence, verify real free Gemma results, record the demo, and approve the final post. No submission, partner qualification, or contest outcome is asserted. Any commits after the deadline must be identified here.

## Credit and provenance

- The verdict-card idea and required `UNVERIFIABLE` outcome originated in the earlier private `KyPython/claim-checker` concept, begun October 17, 2026. This repository is a distinct implementation begun October 22 for the October 19–25 window; originality review remains an owner gate.
- Initial code: **Claude Opus 4.6 (Thinking), via Antigravity**.
- Initial requirements/design/task documentation: **ChatGPT**, AI-authored.
- October 23 completion hardening, regression tests, local verification, and handoff documentation: **OpenAI Codex**, agent-authored and agent-run.
- Independent human code review, review of the bundled source excerpts, and human-run tests are **not evidenced** by agent execution or by an owner commit.
