# Requirements — claim-checker-local (Kiro-style SPEC v2)
Status: **Approved implementation specification; NOT implemented, tested or submitted.**
Last revised: 2026-10-22. Canonical issue: https://github.com/KyPython/claim-checker-local/issues/1

## Requirements authority and operating assumptions

Owner-selected DEV Hacktoberfest Week 3 “Slow and Steady” project. Challenge closes October 25, 2026 at 11:59 PM PDT. The official contest requires a NEW completed project and its repository within Oct 19–25, open-source AI at the core, one DEV submission using #hf26challenge, code link and demo, explanation of why open innovation matters. Offline execution is **NOT required**. The Best Use of Gemma prize accepts Gemma hosted by another provider.

Source rules: https://dev.to/page/hacktoberfest-week3-2026-10-19-contest-rules and https://dev.to/challenges/hf26. No submission eligibility or model usage is asserted without a real receipt.

The owner's ARM64 16 GiB laptop does not currently run Ollama. Do not add a local inference dependency. The development agent may be ANY approved free/included model; the **application** must use the exact free Gemma endpoint and report that accurately. No extra credits or paid capacity.

## Functional requirements (EARS format)

### R01 — Claim input
WHEN a user supplies exactly one claim through `--claim` OR standard input, THE SYSTEM SHALL trim whitespace, enforce nonblank text of at most 2,000 characters, and display the literal input without interpreting embedded instructions as commands. WHEN both modes are supplied, THE SYSTEM SHALL use a documented deterministic precedence or reject the combination.

### R02 — Runtime open-weight model
WHEN the CLI is authorized to invoke inference, THE SYSTEM SHALL send exactly one HTTPS request to `https://openrouter.ai/api/v1/chat/completions` with `model: google/gemma-4-26b-a4b-it:free`. THE SYSTEM SHALL NOT choose `openrouter/free`, a nonfree tag, a closed model, local Ollama, or any paid routing fallback.

### R03 — Secret and permission boundary
WHEN `OPENROUTER_API_KEY` is absent, invalid or refused, THE SYSTEM SHALL exit with a sanitized error, without exposing the key or making a paid-model request. THE SYSTEM SHALL obtain the key from the local process environment only; THE SYSTEM SHALL NOT log/store submitted claims, auth headers or raw provider error bodies. `.env` SHALL be gitignored.

### R04 — Response contract
WHEN the provider responds successfully, THE SYSTEM SHALL parse and strictly validate a card containing `claim`, `verdict`, `rationale`, `what_would_settle_it`, `model`, `evidence_ids` and `disclosure`. Verdict SHALL be precisely one of TRUE, FALSE, MISLEADING, UNVERIFIABLE. Narrative fields SHALL be nonempty and length-bounded. `model` SHALL display the exact configured model tag, and actual provider metadata must not contradict it.

### R05 — Grounding and abstention
WHEN no validated curated evidence was supplied, THE SYSTEM SHALL return only an honest `UNVERIFIABLE` assessment, not factual TRUE/FALSE/MISLEADING based on model memory. WHEN evidence does not entail the intended conclusion, is contradictory, stale for the claim, or lacks provenance, THE SYSTEM SHALL abstain. WHEN a confident verdict is supported by identified, independently reviewed source excerpts, THE SYSTEM MAY return it, with references only to IDs present in the evidence input. THE SYSTEM SHALL NOT fabricate, browse or cite nonexistent sources.

Verdict semantics: **TRUE** means supplied reviewed evidence directly supports the material claim; **FALSE** means it directly contradicts it; **MISLEADING** means the claim contains an evidence-supported element but omits context that materially changes interpretation; **UNVERIFIABLE** means adequate evidence is not available to support any of the others. These are provisional model-assisted classifications, not externally accredited facts.

### R06 — Error semantics
WHEN the provider is unreachable, rate-limited (429), unauthorized (401), requires payment (402), returns a 5xx, times out, returns malformed/partial JSON, or reports an unapproved model, THE SYSTEM SHALL emit an explicit **REQUEST FAILED** outcome with nonzero exit status. THE SYSTEM SHALL NOT disguise a transport/contract failure as a successful UNVERIFIABLE verdict, retry automatically, or silently call another provider.

### R07 — Budget and network safety
WHILE running one user claim, THE SYSTEM SHALL perform no more than one inference call, with a finite timeout. For an opt-in batch eval, calls SHALL be hard-capped by the number of declared cases (at most 8 live cases per run) and disabled when the owner has no confirmed free allowance. THE SYSTEM SHALL avoid analytics, web searches, external URL fetches, CI, deploys, paid services, and background jobs. Daily provider quotas are not a service guarantee.

### R08 — Data/claim privacy
WHEN showing a result, THE SYSTEM SHALL identify it as AI-generated and disclose that the input was sent to a remote provider. THE SYSTEM SHALL NOT claim offline operation, end-to-end privacy, no-provider-retention, or medical/legal/financial authority. WHEN a prompt contains a URL, THE SYSTEM SHALL treat it as text, not fetch or execute it.

### R09 — Golden-case evaluation
THE PROJECT SHALL include at least eight independently reviewed and justified candidate claims with intended coverage across TRUE/FALSE/MISLEADING/UNVERIFIABLE, provenance status, supplied evidence where used, and explicitly allowed honest abstention. Previous toothpaste and banana-cancer rumors are *candidates*; do not assert medical fact-check labels without reviewed authoritative support. THE PROJECT SHALL have deterministic no-API mock unit tests and an explicit opt-in live test against the actual exact free Gemma model, reporting true per-case results and resource counts; the live test cannot be claimed complete before it runs.

### R10 — Originality and credit
THE PROJECT SHALL identify earlier private `KyPython/claim-checker` (idea Oct 17) as the provenance of the verdict-card concept and required UNVERIFIABLE outcome, and SHALL be a significant new implementation in the Oct 19–25 window. Agent-generated code, agent-run tests, human approval and independently human-written work SHALL be attributed separately. Previous private code SHALL NOT be copied or published without review.

### R11 — Demo
WHEN implementation passes acceptance criteria, THE OWNER MAY record a ~60–90-second screen demo showing an actual claim card, honest uncertainty, model identifier and evaluation outcomes. No source-recording footage or spoken narration is required. THE DEMO SHALL NOT simulate results, claim Wi-Fi-off functionality, or leak secrets.

### R12 — Challenge submission
AFTER source originality, functional gates, personal eligibility, active DEV form and owner approval are verified, THE OWNER MAY publish one DEV Week 3 entry using the official template, with `devchallenge`/`hf26challenge` tags, demonstration and public repo URL, factual “How I Built It,” why open innovation matters, and **Best Use of Gemma** only if a live Gemma receipt exists. Never auto-publish, auto-merge, buy capacity, or invent saved time.

## Non-goals
No local AI installation, no Ollama, offline model, live search/citation crawler, mobile app, hosted service, user accounts, automatic paid provider failover, analytics, secret storage, performance claims or unspecified integrations. Optional localhost UI deferred until core gates pass.

## Human approval/stop gates
- PENDING: verified account/key with access to the `:free` endpoint and a non-billed route.
- PENDING: curated evidence source review (avoid medical misinformation).
- PENDING: actual model invocation, eight live outputs and provider metadata verification.
- PENDING: age/location/DEV eligibility, original work check and one published entry.
- Required owner decision for PR push/merge, public announcement, model/provider substitution or purchases.

**Nothing in this document constitutes a passing test or permission to deploy.**
