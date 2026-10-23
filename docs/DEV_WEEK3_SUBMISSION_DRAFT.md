---
title: "Claim Checker: A Slower, Safer First Pass on Claims With Gemma"
published: false
tags: devchallenge, hf26challenge, gemma, python
---

*An unpublished candidate submission for the [Hacktoberfest Open-Source AI Challenge, Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19).*

> **PREPARED FOR DEV — NOT YET PUBLISHED.** The genuine Gemma model demo has been enhanced and uploaded to a verified publicly viewable Google Drive file. The code is merged into `main`. DEV sign-in and competition-entry confirmation remain outstanding; account-specific Google usage cost is unverified.

## What I Built

A small claim on a page can trigger a big research detour: more tabs, more searching, and a temptation to decide before inspecting the source. I wanted a smaller *first step* instead of pretending an AI model alone could do the entire fact-check.

**Claim Checker** is a Python standard-library CLI that asks Google's **open-weight Gemma 4** model for a structured, *provisional* claim-triage card. It reports one of four labels—`TRUE`, `FALSE`, `MISLEADING`, or `UNVERIFIABLE`—alongside a rationale, the evidence identifiers cited, and what would settle an unresolved claim.

The key idea is to **reward useful uncertainty**. The application does not equate a model's memory with independently reviewed evidence. If no source was supplied and reviewed, confident verdicts cannot pass the application validator. The safe outcome is `UNVERIFIABLE`. The benefit is the first structured question to investigate; it is **not** a replacement for independent fact-checking or a live source search.

## Demo

**[Watch the actual Claim Checker Gemma 4 demonstration (2:44)](https://drive.google.com/file/d/1t9qHuGz_YDCVyvgI7sUuAdQLFE8PxwmU/view?usp=drivesdk)**

This is an actual, lightly edited Mac screen recording. The video shows the Google-hosted Gemma response and offline test summaries. Audio and image clarity were improved without generating new claims, changing the model verdict, dubbing speech, or replacing tests. The original is preserved. The Google Drive file has been independently checked through connected metadata as **anyone-with-link / reader**; public playback in a signed-out browser was not separately tested.

**Verified real sample on October 23, 2026:**

```bash
python3 claimcheck.py --provider google --model gemma-4-26b-a4b-it \
  --claim "Earth is the third planet from the Sun." --json
```

The actual validated JSON card reported `model: "gemma-4-26b-a4b-it"`, `provider: "google"`, `verdict: "UNVERIFIABLE"`, `evidence_ids: []`, and explained that no evidence had been supplied to support or contradict the claim. That does **not** mean the astronomy claim is uncertain in reality: it means the application correctly refuses to certify facts without a reviewed source.

**Demo video URL:** [public-viewer Google Drive video](https://drive.google.com/file/d/1t9qHuGz_YDCVyvgI7sUuAdQLFE8PxwmU/view?usp=drivesdk) (2:44, 1080p).

## Code

[KyPython/claim-checker-local](https://github.com/KyPython/claim-checker-local)

Python 3.11+; standard library only. Running the CLI uses a remote provider key held privately in the user's environment. PR #2 was squash-merged to public `main` as commit `0551cd1adab5709d4e4253c8e5adc4b468da4110` on October 23, 2026. The original tested code receipt remains tied to `6e0c2d5`.

## How I Built It

The app uses **Gemma 4 26B A4B IT**, served over HTTPS by **Google's Gemini API**. It does **not** run the model offline. A separate manually chosen route can use pinned free Gemma endpoints through OpenRouter; no automatic failover, paid variant, local GPU or cloud deployment is required. Each claim makes at most one request. The response is checked for expected model identity, completion status, JSON shape, allowed verdict, evidence IDs and grounding limits. Failed or incomplete provider calls produce a nonzero request error—not a fake success.

**Actual Mac verification, October 23:** `git rev-parse --short HEAD` displayed `6e0c2d5`; Python compilation completed without error, deterministic mock evaluation reported **23/23**, and unit tests reported **34/34**. The **real Google Gemma inference** returned a validated `UNVERIFIABLE` card with no supplied evidence. [Receipt and exact outcome](https://github.com/KyPython/claim-checker-local/blob/main/docs/LIVE_GEMMA_RECEIPT_2026-10-23.md).

These tests cover **software contracts and safety behavior**, not measured factual accuracy. Our six candidate source excerpts are **not marked human-reviewed**, and we have **not** completed the proposed eight-case live factual golden evaluation. A `verified_by_human` value in a local file is only an assertion, not proof of source authenticity or entailment.

There were real provider obstacles: OpenRouter's free route returned HTTP 429, then the native Google route returned an HTTP 400 and a response the first parser couldn't use. The Google adapter was corrected to accept multiple *final* text parts while ignoring thinking parts and rejecting incomplete generations. The subsequent independently run Mac tests and a valid live Gemma card are the evidence that this narrower implementation worked.

**Provider cost:** TODO — verify the actual observed request in the relevant Google AI Studio project. Google's price listing is not an individual billing receipt. No claim of $0 actual spend is made yet.

**Attribution:** The initial Python implementation was authored by **Claude Opus 4.6 (Thinking) via Antigravity**, and ChatGPT authored/updated specification, safeguards and subsequent revisions. The user established and reviewed the project concept and executed the cited Mac verification commands. These are distinct from unaided software-writing evidence. The verdict-card format and first-class `UNVERIFIABLE` decision were adapted from an earlier **private** Claim Checker concept begun October 17, 2026. This Week 3 project is a new, separate implementation begun during the October 19–25 challenge window.

## Why Does Open Innovation Matter?

A portable interface to an **open-weight model** lets the project use actual Gemma behavior without binding its claim-validation rules to a proprietary assistant. Hosted inference was an engineering tradeoff for a modest laptop: less local resource cost, but a real dependency on network access, free-tier capacity, provider privacy terms, and correct API response handling.

That is why the uncertain outcome is designed as a first-class result rather than hidden. An AI assessment can help triage *what to check* while leaving the final claim of truth to reviewed sources.

## The Lazy Payoff

The intended time saving is **starting with a structured claim-triage card**, including a suggestion for what primary evidence is needed. I have **not measured** minutes saved or a validated accuracy lift, so there is no invented benchmark here. A future study could compare how long it takes to identify the right follow-up source with and without this tool.

## Prize Categories

**Best Use of Gemma**: The challenge explicitly permits Gemma served through Google Cloud or another provider. A genuine `gemma-4-26b-a4b-it` runtime response was observed on October 23. Entry/category eligibility still depends on a valid submitted article and the organizer's decisions.

**Final publication gate:** Sign into DEV, verify Week 3 still accepts entries, review the exact draft under your account, publish once with `devchallenge` and `hf26challenge`, and record the resulting public DEV URL. Provider cost remains unverified; do not assert $0 account cost.
