# Implementation tasks — claim-checker-local (Kiro-style SPEC v2)
Status: **PARTIALLY EXECUTED — Mac-verified CLI and genuine Gemma 4 model inference at `6e0c2d5` on Oct 23. No final video, cost receipt, source/oracle human review, merge or published DEV submission yet.** Do not check any remaining item off without the corresponding real execution receipt.
Source of truth: [issue #1](https://github.com/KyPython/claim-checker-local/issues/1); [requirements](./requirements.md); [design](./design.md). Deadline: Oct 25, 2026 11:59 PM PDT (Oct 26 02:59 AM ET).

## Latest observed acceptance — October 23, 2026 (overrides earlier PENDING runtime statements)

- [x] **A1/A3/A4/A6/A8 local contract subset:** owner Mac Python compile returned success; deterministic mock suite **23/23**; unit tests **34/34** at code SHA `6e0c2d5`.
- [x] **A2 one real model request:** `python3 claimcheck.py --provider google --model gemma-4-26b-a4b-it --claim "Earth is the third planet from the Sun." --json` returned a **schema-valid** JSON `UNVERIFIABLE` card, `provider=google`, `model=gemma-4-26b-a4b-it`, `evidence_ids=[]` on owner Mac. This is actual hosted Gemma inference and demonstrates a single safe no-evidence path.
- [x] **Failure recovery contract:** previous Google HTTP 400 and multi-part parsing failures did not trigger unapproved retries/paid substitutions; new fail-closed parser regression tests passed.
- [ ] **Cost/entitlement evidence:** Google's public free-only token price does not itself establish actual $0 use for this Google AI Studio project. Obtain redacted account/project usage evidence.
- [ ] **A5 full golden-set accuracy/live batch:** unreviewed source/oracle fixtures remain blocked, not 8/8 verified factual calls; this does not invalidate the limited no-evidence live contract receipt.
- [ ] **A11 working demo:** real successful terminal run exists, but the video still needs recording, review, and an embeddable URL. Follow [verbatim recording script](../../docs/DEMO_RECORDING_PLAN_2026-10-23.md).
- [ ] **A12 challenge publication:** signed-in form, owner eligibility, final article review/approval and publication URL still missing. One submission only.
- [ ] **Release/merge:** independent review and owner merge authorization; status remains **HOLD**.

Evidence: [sanitized real-model receipt](../../docs/LIVE_GEMMA_RECEIPT_2026-10-23.md). The later documentation commits do not invalidate the code-SHA tests; rerun tests for any further **runtime code changes** before release.

## Ownership and execution boundaries

- Spec authoring has been performed by ChatGPT as AI-authored documentation, **not as owner-written code**. Future coding-agent implementation must be attributed to that agent; human design, manual review, personally authored changes and actual human tests may be claimed only when evidenced.
- Current environment: 16 GiB ARM64 Mac, Ollama absent, no current local inference. Don't reinstall local LLM or require airplane mode.
- No paid credits, no cloud CI, no deployments, no silent paid model fallback, no PR/merge/DEV publish without separate owner approval. If an API account/free Gemma endpoint is not accessible, **STOP at mocked tests** and report BLOCKED.
- Check repository instructions and governance before editing; do not modify other `claim-checker` private code or protected governance settings.

## Phase 0 — Preflight (no spend, no git changes)

- [ ] T0.1 Read issue #1, README and these three files; confirm free-only model ID `google/gemma-4-26b-a4b-it:free`, provider `https://openrouter.ai/api/v1/chat/completions`, no local Ollama.
- [ ] T0.2 Verify current free endpoint availability and posted limits in the official provider documentation without sending user secrets to an agent. **Never** create billing or top up to prove availability.
- [ ] T0.3 Identify which available coding agent is operating and log attribution. Verify project checkout is exactly `KyPython/claim-checker-local` and branch permissions. If cannot access repo, return a clean no-write implementation handoff.
- [ ] T0.4 Validate official Week 3 contest rules/template and distinguish project-level eligibility from personal 18+/region/account eligibility. No claim of eligible entry yet.
- **Exit evidence:** preflight report with VERIFIED/BLOCKED/UNKNOWN and source URLs; no fake runtime pass.

## Phase 1 — Core CLI with no-live mocks (R01–R08)

- [ ] T1.1 Implement `claimcheck.py` for `--claim` or stdin, length limits and explicit error codes; no local LLM.
- [ ] T1.2 Build an injectable simple HTTP client using only Python stdlib (or document exactly why small dependency needed). One request only; HTTPS host + free Gemma model ID fixed; 30s timeout; no retry/fallback.
- [ ] T1.3 Read `OPENROUTER_API_KEY` **only** from environment. Create `.gitignore` for local env secrets, virtualenv and output. Ensure no credentials in traces, code, README or Git history.
- [ ] T1.4 Prompt Gemma to produce only structured claim verdict. Parse JSON strictly. Validate enum, human-readable rationale and what-would-settle field, actual provider metadata and allowed evidence IDs. Ensure only code-controlled fields assert configured model/disclosure.
- [ ] T1.5 Implement grounded-evidence rule: no real reviewed source = UNVERIFIABLE or explicit validation error; no hallucinated citations; input treated as data. Return safe error on HTTP 401/402/429/5xx, timeout and model mismatch.
- [ ] T1.6 Test all branches with **offline mocked HTTP**, including provider throws, malicious claim instructions, absent/long input, wrong returned model, JSON schema break and quota exhaustion. Record command and actual test output.
- **Exit evidence:** A1 (local CLI only), A3, A4 mock, A6 mock, A7, A8 source/tests evidenced; A2/A5 live still UNTESTED.

## Phase 2 — Reviewed golden cases and verifiable assessments (R05, R09)

- [ ] T2.1 Create `evals/claims.json` with **at least 8 distinct cases** covering four intended verdict categories. Record `case_id`, `claim`, `expected_verdict`, `allowed_abstain`, evidence IDs and `provenance_reviewed`. **No marked reviewed source unless actually checked**.
- [ ] T2.2 Where a confident TRUE/FALSE/MISLEADING label is desired, provide minimal authoritative/reviewed source evidence and references. Previous toothpaste and banana/cancer claims are unverified candidate prompts, not automatically false. Prefer uncontroversial non-medical facts first. All unsupported cases expect UNVERIFIABLE.
- [ ] T2.3 Implement `evals/run_eval.py` with a fully **mocked default** path; fail if a mock case mismatches its evidence and expected outcome. Explicit `--live` initiates at most 8 real requests, never silent calls in default mode, with per-case actual expected/observed and count. Keep mock vs live results unmistakably labeled.
- [ ] T2.4 Reconcile error budgets and sanity check a live batch uses <=8 total calls; provider free tier advertised 50/day and 20/min, but actual allowance is UNKNOWN. No auto retry or paid route, even when free limit reached.
- **Exit evidence:** A5 mocks PASS only when actually run; A5 live PENDING until actual endpoint test; no "all eight passed" without actual live receipts.

## Phase 3 — Opt-in live hosted-Gemma test (requires verified zero-cost provider access)

- [ ] T3.1 Owner locally provisions or confirms an existing OpenRouter account and env-key without disclosing key to AI/chat/code. Explicitly verify zero-cost Gemma route; if key/model unavailable, mark BLOCKED, do not install Ollama.
- [ ] T3.2 Use exactly one live sample from safe public input; verify HTTP returns actual content and reported model is not different, without leaking headers. Record sanitized model and timing, not secret or provider billing details.
- [ ] T3.3 Demonstrate UNVERIFIABLE for genuinely insufficient evidence, and one honestly evidence-supported sample if curated sources are available. Validate output claims and safe errors.
- [ ] T3.4 Run all eight opt-in live cases only if free budget and time remain, save accurate pass/fail/abstention counts and BLOCKED statuses; don't use artificial "golden" responses as evidence of live Gemma success.
- **Exit evidence:** A2, A4 and A5 live explicitly VERIFIED or BLOCKED, not inferred.

## Phase 4 — Honest documentation and no-narration demo

- [ ] T4.1 Update README to remove prebuild status **only when the app is really implemented**; include prerequisites, setup, `OPENROUTER_API_KEY` handling, exact model tag, command, mock and live eval modes, privacy disclaimer, limitations and actual tests. Credit original private Oct-17 claim-checker idea accurately.
- [ ] T4.2 Check git diff for provider keys, private code, copied text, confidential data, accidental logs, and attribution inflation. Confirm repo created Oct22, code new in window and any reused material significant/credited.
- [ ] T4.3 Record **60–90-second SCREEN DEMO only** after working program: input claim → observed card; insufficient-evidence claim → UNVERIFIABLE; actual Gemma model info; actual test suite result. Captions optional; no filming how the code was produced; no Wi-Fi-off pretense.
- [ ] T4.4 Prepare DEV template sections based on **real** outcomes: What I Built, Demo, Code, How I Built It, Why Does Open Innovation Matter?, Prize Categories (Gemma if proven). Agent Session OPTIONAL, Lazy Payoff OPTIONAL if real measured time saved. No invented quote or benchmark.
- **Exit evidence:** A9–A11, README accurate, video exists, no publish yet.

## Phase 5 — Final human approval and submission (R12)

- [ ] T5.1 Owner reviews file-by-file implementation diff, security/no-spend record, source citations, original vs borrowed parts, and A1–A12 results.
- [ ] T5.2 Owner separately authorizes and performs (or explicitly delegates) PR/push/merge as appropriate to existing repo policies. A working README/docs change is not evidence that product code passed.
- [ ] T5.3 Owner confirms personal participation eligibility and live DEV form. One submission only, `#hf26challenge` tag, code link, demo, accurately evidenced Best Use of Gemma. Submit by deadline with explicit owner authorization. Note any post-deadline commits in README.
- [ ] T5.4 Verify actual published DEV post URL and record its publication timestamp; until this exists, status **NOT SUBMITTED**.
- **Exit evidence:** real published post/link and receipts, or HOLD. No implied contest result or winner status.

## Reviewer handoff format

At the end of the coding agent's attempt, report:
1. Exact repository branch, commit and agent identity.
2. Changed files and diff summary.
3. Table of **A1–A12** each with DONE, FAILED, UNTESTED or BLOCKED; runnable command and actual result. Never equate mocked integration with live endpoint verification.
4. Provider/model/cost check and actual counts. Mask keys and any private claims.
5. Originality/credit/disclosure checklist, known gaps and one next human decision.
6. **Explicit STOP** on absent credit-free API availability, unreviewed evidence, fail-open secret exposure, or missing owner gate.

This plan does not authorize API purchases, CI runs, automatic PRs, merges, deployments, or DEV posting.


## Release-routing delta — 2026-10-23 (owner-approved scope, execution pending)

- [x] Document official DEV rules: overall submission can use other qualifying open-source AI, but Best Use of Gemma requires Gemma; created challenge project remains separate from private original.
- [x] Stage explicit allowlisted OpenRouter 31B free and Google native 26B/31B routes on current hardening PR branch; do not infer runtime success from commit.
- [x] Stage ten new offline tests of exact model routing, no-key zero calls, Google modelVersion checks, schema and evidence gates; execution pending.
- [x] Executed on Mac at SHA `6e0c2d5`: Python compilation, **23/23** offline mocks, **34/34** unittests; includes the additional post-25 Google response parsing tests.
- [ ] Verify AI Studio Gemma free-tier project and quotas without giving keys to agent. Google free-tier data-use disclosure remains mandatory.
- [x] One valid real Google Gemma 4 26B inference generated a contract-valid `UNVERIFIABLE` card at `6e0c2d5`. [Receipt](../../docs/LIVE_GEMMA_RECEIPT_2026-10-23.md). **Billing/usage proof is separate and still pending.**
- [ ] Only with a real model result, record actual 60–90s functional demo; no simulated verdict or synthetic input as purported real inference.
- [ ] Complete source/oracle review for any case claimed TRUE/FALSE/MISLEADING; keep false flags otherwise. Eight live-case evaluation remains pending under existing A5 gate.
- [ ] Confirm DEV signed-in submission template, owner eligibility and publication authorization; publish once before October 25 11:59 PM PDT, record actual URL. Release blocked until all applicable gates have receipts.

No CI, PR merge, paid call, public deployment or contest submission is authorized solely by staging this code.


## 2026-10-23 14:48 ET — executed Mac receipts and new blocker

- [x] At tested SHA `249e900`: Python compile pass; deterministic mock **23/23**; unittest discovery **25/25**.
- [x] Exactly two manually initiated Google native Gemma 4 26B calls observed: first **HTTP 400**; second reached response parser with matching modelVersion but no single usable final text candidate. **These are attempted calls, not validated verdicts**.
- [x] Stage corrective Google multipart final-text extraction, thought-only/cutoff rejection, minimal-thinking configuration and sanitized 400 category. Additional new tests are staged.
- [x] All current code regression checks at SHA `6e0c2d5`: 23/23 offline checks, 34/34 unittests, and Python compilation passed.
- [x] Actual Google-hosted Gemma 4 26B card returned with exact validated model identity and no evidence. [x] Owner submitted claim privately through hidden-key environment procedure. [ ] Confirm separate project free-tier entitlement and per-request cost; **no more calls required for this narrow live-path receipt**.
- [ ] Human source/oracle review, actual live screen demo, DEV signed-in form, publication approval and receipt still pending.
