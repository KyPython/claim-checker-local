---
title: "Claim Checker: A Slower, Safer First Pass on Claims With Gemma"
published: false
tags: devchallenge, hf26challenge, gemma, python
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19).*

> **DRAFT — NOT APPROVED FOR PUBLICATION.** Replace every TODO below only with observed results. Verify DEV eligibility and signed-in submission access. Do not publish a mocked demo as a real Gemma call.

## What I Built

A post can make a factual claim in one sentence. Checking it often takes several new tabs, a search, and a judgment about which sources deserve trust. That friction is why I wanted a simpler first pass.

**Claim Checker** is a small Python command-line application: supply one claim, and it asks an open-weight Gemma model to produce a structured **provisional verdict card**. The card includes a classification (TRUE, FALSE, MISLEADING or UNVERIFIABLE), a short rationale, and what evidence would settle the issue.

The important design decision is **UNVERIFIABLE**. When no evidence is supplied, the app must not present the model's memory as a fact-check. It is a tool for deciding *what to investigate next*, not a truth machine.

This Week 3 project is a new implementation built during the challenge window, and builds on the verdict-card/UNVERIFIABLE idea from my earlier private October 17 claim-checker experiment.

## Demo

**TODO AFTER REAL RUN:** Embed or link a 60–90-second screen recording of the actual CLI making an actual Gemma request. Show the command, returned verdict card, model metadata, and a no-evidence UNVERIFIABLE example. Hide the API key and personal information. If the free endpoint or authenticated contest form is unavailable, do not substitute mock output.

Observed live demo date and exact runtime result: **NOT YET AVAILABLE — HTTP 429 on final observed Gemma requests (October 23, 2026).**

## Code

[KyPython/claim-checker-local](https://github.com/KyPython/claim-checker-local)

Run with Python 3.11+; standard library only. The README documents the setup. An OpenRouter key is required for live inference and stays in the local environment.

## How I Built It

The runtime is **Gemma 4**, requested at the fixed OpenRouter endpoint with model ID `google/gemma-4-26b-a4b-it:free`. This project does **not** run inference offline: the input is sent over HTTPS to a remote provider.

The CLI makes one bounded request per claim, with no automatic retry, paid model fallback, or model auto-router. It validates a fixed verdict schema and rejects mismatched/missing model identity, unsupported confident verdicts, invented evidence IDs and malformed output. Evidence excerpts are user-supplied; the app does not browse for sources.

**Honest test status** (from actual Mac terminal output):

**Observed on owner's Mac, October 23, 2026, Python 3.12.2, hardening branch at `70dbf31`:** `python3 -m py_compile claimcheck.py evals/run_eval.py evals/test_release_contract.py` completed without reported error. `python3 evals/run_eval.py -v` reported **23/23 deterministic mock checks passing** (eight fixture verdict contracts, 15 synthetic validation/input failures). `python3 -m unittest discover -s evals -p 'test_*.py' -v` reported **15/15 passing**. The mock cases with unreviewed evidence correctly blocked confident verdicts; none of this establishes source truth or live Gemma accuracy. Account API-key validation via `GET /api/v1/key` returned HTTP **200**. Attempted live claim checks returned HTTP **401** twice and **429** twice; **zero successful Gemma inference requests** are evidenced. The activity dashboard showed one unrelated Nemotron request at $0.00, **not Gemma cost or proof**. No provider-paid fallback is allowed. The original six source excerpts are still marked `verified_by_human=false`; human source adjudication remains pending.

**Release gate:** Until a successful, exact-model `google/gemma-4-26b-a4b-it:free` request and its account activity/cost are verified, do **not** insert a live-verdict screenshot, claim a fully functioning Gemma demo, mark A2/A5-live/A11 complete, assert the Best Use of Gemma runtime was demonstrated, or publish this post as though Gemma ran. A separate clearly labeled engineering screen capture of offline tests is acceptable *as supporting footage only*.
- Offline deterministic mocks test code paths and failure handling; they do **not** establish factual accuracy.
- Golden claim labels cannot count as source-grounded truth until the original excerpts and expected judgments are independently reviewed.
- A live Gemma run and no-cost receipt are necessary before claiming this demo works end to end.

Known limitation: even a reviewed-source flag in local JSON does not independently prove that an excerpt entails the claim. The model's classification remains preliminary.

**Development attribution:** Coding agent Claude Opus 4.6 (Thinking) via Antigravity authored the first Python implementation; ChatGPT helped produce the specification and reviewed code/tests. The owner's original idea, source review, real-run outcomes and final publication must be attributed distinctly. Do not represent AI-authored code as an unaided implementation.

## Why Does Open Innovation Matter?

An open-weight model lets the application use an AI core without tying its entire design to a closed proprietary model. Here the intentionally constrained cloud route avoids a large local model download on a modest laptop. Open-weight **does not mean** offline, private by default, always free or independent of the provider.

I chose explicit uncertainty and failure over a confident-looking answer that cannot be defended. A useful result is sometimes a clear explanation of *what we still need to know*.

## The Lazy Payoff

I can collect the first structured question about a claim in one command rather than manually drafting a research checklist. **I have not measured verified time savings**, so I am not attaching a fabricated percentage. The real benefit to test is whether this shortens the *triage* step without encouraging people to skip source verification.

## Prize Categories

**Best Use of Gemma** — contingent on a documented, genuine Gemma runtime call. Do not claim category eligibility if the live model check does not pass.

<!-- Final human checklist: signed-in DEV template opens; real demo link; exact observed model & provider cost; redaction; reviewed fixture results; user approves publish; tags devchallenge and hf26challenge; deadline October 25 11:59 PM PDT. -->


### October 23 amendment — provider choice is source-backed, runtime remains unverified

The challenge does **not** mandate a specific Gemma variant or OpenRouter. Official competition rules permit open-source AI generally, and the **Best Use of Gemma** category accepts Gemma hosted through another provider. The public repository now includes a **manual**, no-auto-fallback option to use Google-hosted Gemma 4 26B/31B through the native Gemini API, as well as explicitly selected OpenRouter free Gemma 31B. Google [pricing](https://ai.google.dev/gemini-api/docs/pricing) lists Gemma 4 free-only input/output tokens, and Google [API docs](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api) document the native route. Free-tier submissions may be used to improve the provider's products.

**Do not claim this alternative worked yet.** The extra provider code and ten new mocked route tests have not yet been rerun on Mac, and no real provider response, model metadata, usage/cost or successful filming receipt has been observed. Update the above prose to match the **actual manually selected provider/model** once that has been demonstrated; leave this post unpublished meanwhile.
