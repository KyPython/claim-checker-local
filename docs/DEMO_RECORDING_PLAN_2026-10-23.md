# Claim Checker — screen-recording plan and exact narration (2026-10-23)

**Status:** Production Gemma demo cannot be recorded as successful while OpenRouter returns 429. This is an **engineering walkthrough only**, not the official A11 live-model acceptance demo. Keep the filmed truth separate from mocked tests. No API key on screen. Record no actual private claims or paid calls.

## Clip A — truthful engineering preview, 75–90 seconds (can record now)

Screen: Terminal in `~/claim-checker-local` on `audit/release-hardening-2026-10-22`, no secret entry shown. Make terminal font readable.

**0:00–0:12 — Face/voice or a title slide. Read verbatim:**
"I built a small claim-triage CLI for Hacktoberfest's Slow and Steady challenge. The goal is one structured first pass instead of having to invent the research checklist yourself."

**0:12–0:25 — Show `python3 claimcheck.py --help`. Read:**
"The project is Python standard library only. It accepts a claim, produces a structured provisional card, and reserves decisive claims for evidence that has actually been reviewed."

**0:25–0:48 — Run `python3 evals/run_eval.py -v`. Read:**
"These are deterministic mocks, not Gemma outputs. Eight fixture contracts and fifteen synthetic error cases passed on my Mac, including rejecting invented evidence IDs and the wrong model."

**0:48–1:02 — Run `python3 -m unittest discover -s evals -p 'test_*.py' -v`. Read:**
"Fifteen regression checks also passed. The app rejects unreviewed sources rather than inventing a confident fact-check."

**1:02–1:19 — Show the README fixed-model and error-handling sections, not a fabricated verdict. Read:**
"The intended runtime is Google's open-weight Gemma 4 through OpenRouter's exact free endpoint. My key is authenticated, but the free provider has returned HTTP 429, so live inference is not yet verified."

**1:19–1:29 — Show `docs/DEV_WEEK3_SUBMISSION_DRAFT.md` with unpublished status. Read:**
"That limit is part of the engineering story. I will not pass off simulated outputs as a real model demonstration or switch to a paid route."

If recording at normal cadence exceeds 90 seconds, shorten pauses, not disclosures. Avoid any screen showing `OPENROUTER_API_KEY`, an API-key value, sensitive prompts or local personal files.

## Clip B — official A11 Gemma proof (HOLD until actual success)

**Prerequisites:** Reviewed exact `:free` model route, a dedicated properly restricted key, owner-approved one-call live attempt only after provider restriction clears, and no paid fallback. Never automatically retry.

Record the **actual** `python3 claimcheck.py --claim "Earth is the third planet from the Sun." --json` result and inspect its returned model tag and `UNVERIFIABLE` semantics (no source supplied). Capture OpenRouter Activity with exact model and recorded cost; hide account details.

Verbatim narration *only if actually observed*:
"Now this is a real Gemma response from the exact free endpoint. Because I supplied no independently reviewed evidence, the app allows only an UNVERIFIABLE provisional card, not a confident claim of truth. Here is the model identifier and the actual recorded usage cost."

If the response is HTTP 429/401/other failure, do **not** read the success script. Read instead: "The provider refused the call, and the app failed closed. No live Gemma verdict was produced."

## Release checklist

- [x] Mac mock 23/23, unittest 15/15, compile no error (owner terminal output; exact SHA 70dbf31).
- [x] API-key status check returned HTTP 200; never include key.
- [ ] One real successful Gemma response on exact `:free` route with safe model identity.
- [ ] Per-call cost record shows zero and no alternative paid provider.
- [ ] Human review of source excerpts/ground-truth labels or explicitly exclude uncertain cases.
- [ ] Approved demo linked/embedded in DEV template and authenticated submission access verified.
- [ ] Owner approves final publication; published DEV entry receipt is recorded.

Reference: [issue #1](https://github.com/KyPython/claim-checker-local/issues/1); [hardening PR #2](https://github.com/KyPython/claim-checker-local/pull/2); [official challenge](https://dev.to/challenges/hacktoberfest-week3-2026-10-19). Do not copy code from the private original project.


## Approved alternate real-model route (added 2026-10-23)

The recording no longer depends uniquely on OpenRouter. The repo now stages an **explicit Google-hosted Gemma 4** route. When the owner confirms their AI Studio **free-tier** project, obtains a key privately, pulls the current hardening branch and runs the offline checks, the proposed **single** live call is:

```bash
cd "$HOME/claim-checker-local"
git fetch origin audit/release-hardening-2026-10-22
git switch audit/release-hardening-2026-10-22
git pull --ff-only
python3 -m py_compile claimcheck.py evals/run_eval.py evals/test_release_contract.py evals/test_release_gate.py evals/test_provider_routing.py
python3 evals/run_eval.py -v
python3 -m unittest discover -s evals -p 'test_*.py' -v
read -rs "GEMINI_API_KEY?Google AI Studio key (hidden): "
echo
export GEMINI_API_KEY
python3 claimcheck.py --provider google --model gemma-4-26b-a4b-it --claim "Earth is the third planet from the Sun." --json
unset GEMINI_API_KEY
```

Only after real-model response, modelVersion and provider usage are verified may Clip B be recorded with a truthful claim of live Gemma operation. If the response fails, preserve a failure clip as such; don't read the success narration or claim the Best Use of Gemma integration was exercised. Google free-tier data use/remote processing must be mentioned in the DEV post. No provider auto-retry or billing upgrades.
