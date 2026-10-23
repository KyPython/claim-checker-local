# claim-checker-local

**Status (October 23, 2026):** Owner Mac independently ran the code at SHA `70dbf31`: **23/23 offline mocks**, **15/15 unittests**, Python compilation succeeded. Authentication GET /api/v1/key returned HTTP **200**, but live Gemma requests returned **401/429** with **no successful inference**. A subsequent explicit free-Gemma provider/model routing change and eight additional routing tests are now committed **but unexecuted**. Source evidence has not been human-adjudicated, and no actual Gemma demo or DEV publication is verified. **NOT READY FOR FINAL RELEASE.**

A small **Python claim-triage CLI** for the [DEV Hacktoberfest Open-Source AI Challenge, Week 3 — Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19), with the **Best Use of Gemma** category as a conditional entry. The runtime sends a claim to **cloud-hosted open-weight Gemma** through an explicitly selected free-only provider, returning an **AI-generated, preliminary** verdict card with honest `UNVERIFIABLE` handling. **It is not a source-grounded, authoritative fact checker without reviewed evidence.**

## Quick start

### Prerequisites

- **Python 3.11+** (standard library only — no pip install needed)
- An [OpenRouter](https://openrouter.ai/) key **or** a Google [AI Studio](https://aistudio.google.com/apikey) key from a verified free-tier project. Do not enter a paid project or reveal keys.
- No local AI download, no Ollama, no offline model required

### Setup

```bash
# Clone the repository
git clone https://github.com/KyPython/claim-checker-local.git
cd claim-checker-local

# Set your OpenRouter API key (never commit this)
export OPENROUTER_API_KEY="your-key-here"
```

### Run a claim check

```bash
# Via --claim flag
python3 claimcheck.py --claim "Earth is the third planet from the Sun."

# Via stdin
echo "Pluto is a full planet." | python3 claimcheck.py

# With reviewed evidence file
python3 claimcheck.py --claim "Earth is the third planet from the Sun." \
  --evidence-file evals/evidence.json

# JSON output
python3 claimcheck.py --claim "Some claim" --json
```

### Explicit free Gemma provider/model choices — approved October 23

The default remains `google/gemma-4-26b-a4b-it:free` on OpenRouter. Approved additional **manual**, free-only choices are:

| Provider | `--model` | Private environment key | Service |
| --- | --- | --- | --- |
| `--provider openrouter` | `google/gemma-4-26b-a4b-it:free` (default) | `OPENROUTER_API_KEY` | OpenRouter |
| `--provider openrouter` | `google/gemma-4-31b-it:free` | `OPENROUTER_API_KEY` | OpenRouter |
| `--provider google` | `gemma-4-26b-a4b-it` (default for Google) | `GEMINI_API_KEY` | Native Google generateContent |
| `--provider google` | `gemma-4-31b-it` | `GEMINI_API_KEY` | Native Google generateContent |

No automatic retries, fallback, unapproved provider/model, paid route or cross-provider credential reuse. Failures remain nonzero. OpenRouter must return the exact `:free` model; Google must return the exact `modelVersion`. These controls require *actual* live verification. Google [official Gemma API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api) supports both named Gemma 4 models, and [current Google pricing](https://ai.google.dev/gemini-api/docs/pricing) lists Gemma 4 token prices as **free-only**; confirm your project tier and quotas in AI Studio before using its key. Free-tier data may be used by Google to improve its products.

**One explicit Google Gemma call (never repeated automatically):**

```bash
cd "$HOME/claim-checker-local"
git fetch origin audit/release-hardening-2026-10-22
git switch audit/release-hardening-2026-10-22
git pull --ff-only
read -rs "GEMINI_API_KEY?Google AI Studio key (hidden): "
echo
export GEMINI_API_KEY
python3 claimcheck.py --provider google --model gemma-4-26b-a4b-it --claim "Earth is the third planet from the Sun." --json
unset GEMINI_API_KEY
```

A valid response without supplied reviewed evidence should be `UNVERIFIABLE`, not a confident fact-check. If response/model metadata or free-tier eligibility is missing, **stop**. Do not fake the model result.

### Run evaluations

```bash
# Mock tests (offline, no API key needed, deterministic)
python3 evals/run_eval.py

# Mock tests with verbose output
python3 evals/run_eval.py -v

# Additional release-contract regression tests (no network)
python3 -m unittest discover -s evals -p 'test_*.py' -v

# Compile check (no network)
python3 -m py_compile claimcheck.py evals/run_eval.py evals/test_release_contract.py

# Live tests against real Gemma endpoint (requires API key, opt-in only)
python3 evals/run_eval.py --live
# Only after independent human case/source review:
python3 evals/run_eval.py --live --provider google --model gemma-4-26b-a4b-it
```

## How it works

1. **Input validation**: Accepts a single claim via `--claim` or stdin. Trims whitespace, enforces 2,000-character limit, rejects blank input.
2. **Evidence loading** (optional): Reads a curated JSON evidence file with reviewed source excerpts.
3. **Prompt construction**: Builds a structured prompt with the claim as DATA (not instructions) and any supplied evidence.
4. **Inference**: Sends exactly one HTTPS request to `https://openrouter.ai/api/v1/chat/completions` with the fixed model `google/gemma-4-26b-a4b-it:free`.
5. **Response validation**: Strictly validates the response JSON: enum verdict, non-empty rationale, evidence IDs only from supplied sources, **exact free model tag** (missing/stripped :free fails), and sanitization of malformed model-output errors.
6. **Grounding rule**: A confident verdict requires cited evidence IDs with explicit `verified_by_human=true` source declarations and complete basic metadata. Unreviewed fixtures cannot produce a confident card. **Important:** local review flags are user assertions, not cryptographic or semantic proof that the evidence is true, timely, authentic or logically entails a verdict. Human source/adjudication checks remain necessary.

### Verdict semantics

| Verdict | Meaning |
|---|---|
| **TRUE** | Supplied reviewed evidence directly supports the claim |
| **FALSE** | Supplied reviewed evidence directly contradicts the claim |
| **MISLEADING** | Evidence supports part of the claim but omits material context |
| **UNVERIFIABLE** | Evidence is absent, insufficient, or inadequate |

These are **provisional AI-assisted classifications**, not externally accredited facts.

### Error handling

| Condition | Behavior |
|---|---|
| No API key | Configuration error, no HTTP call, exit 1 |
| Blank/too-long input | Input error, no HTTP call, exit 1 |
| HTTP 401/402 | REQUEST FAILED with specific message, exit 1 |
| HTTP 429 | REQUEST FAILED: rate limited, exit 1 |
| Timeout / 5xx | REQUEST FAILED: provider error, exit 1 |
| Malformed JSON | REQUEST FAILED: parse error, exit 1 |
| Wrong model returned | REQUEST FAILED: model mismatch, exit 1 |
| Fabricated source IDs | REQUEST FAILED: validation error, exit 1 |
| Confident verdict without evidence | REQUEST FAILED: grounding violation, exit 1 |

HTTP failures are never disguised as successful `UNVERIFIABLE` verdicts. Exit code 0 only on a schema-valid, successfully processed verdict card.

## Test suite

The evaluation suite (`evals/run_eval.py`) includes:

- **8 candidate verdict cases**: 3× TRUE, 2× FALSE, 1× MISLEADING, 2× UNVERIFIABLE. The disputed ocean case was corrected to TRUE. All eight `provenance_reviewed` flags remain false pending actual review.
- **11 error-handling tests**: HTTP 401/402/429/500, timeout, unreachable, malformed JSON, wrong model, missing fields, fabricated source IDs, confident verdict without evidence
- **4 input validation tests**: blank claim, too-long claim, null claim, missing API key
- **12 new strict-model/provenance/error-sanitization contract tests** staged for independent execution (not yet run)

**Historical coding-agent-reported mock results on pre-hardening main (23/23; independent rerun still required; NOT proof of factual accuracy):**
```
Mock verdict cases: 8/8 passed
Validation tests: 15/15 passed
Total: 23/23 passed
```

Release hardening at SHA 70dbf31: **EXECUTED on Mac (23/23 mocks; 15/15 unittests)**. New provider-routing code/tests after that SHA: **NOT YET EXECUTED.** With existing review flags false, positive mock cases now verify that confident model responses are rejected, rather than certifying truth. Live Gemma test results: **PENDING** — requires owner opt-in with a verified free API key. Live golden sourced cases are blocked until the person reviewing them actually approves the evidence. Do not represent mock verdict outputs as runtime inference or factual accuracy.

**Release blockers after code hardening (Oct 22):** Response model must now match the exact `:free` tag; a provider that reports a base-model alias (or omits the field) will cause a safe failure, and actual billing-route verification is still needed. Evidence human-review flags and claim provenance remain false. Case 06 was relabeled TRUE, but sources have not been independently human-adjudicated. The first hardening code SHA 70dbf31 was actually run on the owner's Mac (23 mocks plus 15 unittests passed); the newer provider-routing changes have NOT been run there. Unrelated or contradictory evidence is not semantically proven safe by schema validation; human review remains essential. See issue #1. Draft DEV post (NOT to publish as-is): [docs/DEV_WEEK3_SUBMISSION_DRAFT.md](docs/DEV_WEEK3_SUBMISSION_DRAFT.md).

## Fixed model and provider

- **Default model**: `google/gemma-4-26b-a4b-it:free`. Only other allowlisted manual free Gemma selections in the table above.
- **Provider**: OpenRouter HTTPS API default or Google native hosted Gemma API when explicitly selected.
- **No automatic fallbacks**: No `openrouter/free` router, no paid models, no local Ollama, no closed models.
- **Budget**: One inference call per claim; eval capped at 8 live cases per run

## Privacy and limitations

> **⚠ Important:**
> - Claim text is sent to a **remote inference provider** (OpenRouter → Gemma). Do not submit secrets, confidential information, or sensitive personal data.
> - This tool does **not** claim offline operation, end-to-end privacy, or zero provider retention.
> - Results are **AI-generated preliminary assessments**, not medical, legal, or financial advice.
> - Real-model outputs are **provisional**, not independent fact-checks.
> - Free-tier rate limits and availability may change without notice; daily provider quotas are not guaranteed.

## File structure

```
claimcheck.py              # CLI and core logic (stdlib only)
evals/
    claims.json            # 8 golden evaluation cases
    evidence.json          # Curated evidence excerpts with provenance
    run_eval.py            # Mock + opt-in live evaluation runner
    test_provider_routing.py # Eight new offline route tests (pending execution)
specs/
    claim-checker-local/
        requirements.md    # R01–R12 requirements (EARS format)
        design.md          # Architecture and output contract
        tasks.md           # Phased implementation tasks
.gitignore                 # Excludes .env, __pycache__, etc.
README.md                  # This file
```

## Canonical specification

See **[GitHub issue #1 — SPEC v2](https://github.com/KyPython/claim-checker-local/issues/1)** for the complete implementation prompt, architecture, security/privacy conditions, A1–A12 acceptance tests, golden claim evaluation contract, demo requirements and submission gate.

## Credit and provenance

- **Verdict-card concept and mandatory UNVERIFIABLE outcome**: Adapted from earlier **private** project `KyPython/claim-checker` (concept begun October 17, 2026).
- **This implementation**: New and distinct, begun October 22, 2026 using cloud-served Gemma, during the contest window (Oct 19–25).
- **Implementation agent**: Claude Opus 4.6 (Thinking) via Antigravity — agent-generated code, attributed here.
- **Spec authoring**: ChatGPT as AI-authored documentation (requirements.md, design.md, tasks.md).
- **Owner review and approval**: Owner committed the agent's work; independent human review of these exact source excerpts, security conditions and final results is **not yet evidenced**.

## Challenge deadline

Submit **one** post through DEV's Week 3 template with the `#hf26challenge` tag, a working video **or** deployed demo, a code link, open-source AI explanation, and properly attributed build notes by **October 25, 2026, 11:59 PM PDT**. A video may be a **60–90-second demonstration of functionality**, not a coding-process recording.

Changes committed *after* the contest deadline must be identified here if any occur.
