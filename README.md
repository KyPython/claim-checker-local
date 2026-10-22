# claim-checker-local

**Status: Implemented — mock tests passing; live Gemma endpoint test PENDING owner opt-in.**

A small **Python claim-triage CLI** for the [DEV Hacktoberfest Open-Source AI Challenge, Week 3 — Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19), with the **Best Use of Gemma** category as a conditional entry. The runtime sends a claim to **cloud-hosted open-weight Gemma** via OpenRouter, returning an **AI-generated, preliminary** verdict card with honest `UNVERIFIABLE` handling. **It is not a source-grounded, authoritative fact checker without reviewed evidence.**

## Quick start

### Prerequisites

- **Python 3.11+** (standard library only — no pip install needed)
- An [OpenRouter](https://openrouter.ai/) account with access to the free Gemma endpoint
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

### Run evaluations

```bash
# Mock tests (offline, no API key needed, deterministic)
python3 evals/run_eval.py

# Mock tests with verbose output
python3 evals/run_eval.py -v

# Live tests against real Gemma endpoint (requires API key, opt-in only)
python3 evals/run_eval.py --live
```

## How it works

1. **Input validation**: Accepts a single claim via `--claim` or stdin. Trims whitespace, enforces 2,000-character limit, rejects blank input.
2. **Evidence loading** (optional): Reads a curated JSON evidence file with reviewed source excerpts.
3. **Prompt construction**: Builds a structured prompt with the claim as DATA (not instructions) and any supplied evidence.
4. **Inference**: Sends exactly one HTTPS request to `https://openrouter.ai/api/v1/chat/completions` with the fixed model `google/gemma-4-26b-a4b-it:free`.
5. **Response validation**: Strictly validates the response JSON: enum verdict, non-empty rationale, evidence IDs only from supplied sources, model tag verification.
6. **Grounding rule**: Without reviewed evidence, only `UNVERIFIABLE` is accepted. The model cannot give a confident TRUE/FALSE/MISLEADING verdict based on training data alone.

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

- **8 golden verdict cases**: 2× TRUE, 3× FALSE, 1× MISLEADING, 2× UNVERIFIABLE
- **11 error-handling tests**: HTTP 401/402/429/500, timeout, unreachable, malformed JSON, wrong model, missing fields, fabricated source IDs, confident verdict without evidence
- **4 input validation tests**: blank claim, too-long claim, null claim, missing API key

**Mock test results (23/23 passing):**
```
Mock verdict cases: 8/8 passed
Validation tests: 15/15 passed
Total: 23/23 passed
```

Live Gemma test results: **PENDING** — requires owner opt-in with a verified free API key.

## Fixed model and provider

- **Model**: `google/gemma-4-26b-a4b-it:free` (exact API ID, no substitution)
- **Provider**: OpenRouter HTTPS API only
- **No fallbacks**: No `openrouter/free` router, no paid models, no local Ollama, no closed models
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
- **Owner review and approval**: Human — independently reviewed and authorized.

## Challenge deadline

Submit **one** post through DEV's Week 3 template with the `#hf26challenge` tag, a working video **or** deployed demo, a code link, open-source AI explanation, and properly attributed build notes by **October 25, 2026, 11:59 PM PDT**. A video may be a **60–90-second demonstration of functionality**, not a coding-process recording.

Changes committed *after* the contest deadline must be identified here if any occur.
