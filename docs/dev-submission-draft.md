---
title: "claim-checker-local: a small claim-triage CLI that can abstain"
published: false
tags: devchallenge, hf26challenge
---

**UNPUBLISHED DRAFT — NOT READY TO SUBMIT.** Live Gemma inference, independent
source review, human code review, the video, eligibility confirmation, and owner
approval are pending. Replace every `PENDING` item with a real receipt or revise
the claim before publication. This file does not authorize publication.

Draft structure follows the Submission Template linked from the
[official Week 3 challenge page](https://dev.to/challenges/hacktoberfest-week3-2026-10-19),
checked October 23, 2026. The signed-in owner's active form still needs checking.

*Draft for the Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady.*

## What I Built

I built a small Python command-line tool for preliminary claim triage. It is
designed to send one claim and optional source excerpts to cloud-hosted Gemma
through OpenRouter, then present a verdict, a short rationale, and what would
settle the question.

The useful constraint is its ability to stop: without a separately supplied
independent review receipt, only `UNVERIFIABLE` is allowed. A receipt binds the
exact claim and approved label to the source content. It is a local trust
decision, not proof of the reviewer's identity. Provider or schema failures are
explicit errors rather than successful-looking uncertainty cards.

The intended benefit is less repetitive formatting during a first pass through
a claim. Checking sources and making the independent judgment still require
work. I have not measured time saved or established factual accuracy.

**PENDING — replace this with the actual live behavior observed on the final
revision. The current offline checks alone do not demonstrate Gemma execution.**

## Demo

**PENDING — insert a real 60–90-second screen video or working deployed demo
link. No video has been recorded for this draft; no deployed service is claimed.**

The [recording checklist](demo.md) calls for an actual source-bound claim card,
an evidence-free abstention, clearly labeled offline results, the exact observed
model identifier, and the remote-inference disclosure.

**PENDING — insert the real capture date, Git revision, observed results, and
sanitized live receipt link. Never substitute test fixtures for a real run.**

## Code

[claim-checker-local on GitHub](https://github.com/KyPython/claim-checker-local)

The implementation uses Python 3.11+ and its standard library. The CLI,
candidate evidence, offline evaluation, regression tests, and written
specifications are in the repository.

**PENDING — confirm the public repository includes the final reviewed revision
and link that exact commit. Confirm the repository's license and originality
before describing any code as reusable open source.**

## How I Built It

The runtime is pinned to `google/gemma-4-26b-a4b-it:free` through the fixed
OpenRouter HTTPS endpoint. The CLI has no local model dependency. A valid claim
permits at most one inference request, with a finite timeout, zero-price routing
limits, no retries, and no paid/model fallback. These settings are controls,
not a guarantee of account allowance or proof that a request ran.

I started from written requirements and a design. The verdict-card idea and
mandatory `UNVERIFIABLE` outcome came from the earlier private
`KyPython/claim-checker` concept, begun October 17, 2026. This repository's distinct
implementation began October 22 during the October 19–25 window. Originality and
any reused material still need owner review.

Claude Opus 4.6 (Thinking), through Antigravity, generated the initial code.
ChatGPT authored the initial specification documents. OpenAI Codex performed the
October 23 completion hardening, wrote regression tests and handoff documentation,
and ran local checks. Those are agent contributions; they are not evidence of
human-written code, independent human code review, or human-run tests.

The offline evaluation uses eight unreviewed candidate cases. All eight currently
allow only abstention. Separate synthetic receipts test the confident-label
boundary without pretending that a human reviewed those sources. Mock tests
check the program's validation and error handling, not the model's factual
accuracy.

The eventual live evaluation can read real per-case receipts with `--review-dir`.
Each receipt binds the exact case and its selected source subset, and every
supplied receipt is validated before any live attempt. Missing receipts keep
their cases unreviewed; reviewed coverage is reported separately from abstention.
No real review receipts have been supplied for this draft.

**PENDING — add the final revision's actual local check results from the
[verification receipt](verification-2026-10-23.md), the owner's independent review
record, and the real live Gemma outcomes and request counts. Do not claim a
benchmark or successful model run until these exist.**

## Why Does Open Innovation Matter?

An open-weight model gives this project a model choice whose weights can be
studied and run outside one closed-model vendor's service. The small application
also makes its prompt, validation rules, and abstention boundary visible in code.
That matters for a tool where a polished answer can otherwise conceal missing
evidence.

This particular implementation still depends on remote OpenRouter inference.
It does not provide offline execution or keep submitted claims off other
people's servers. Its pinned route also does not implement model swapping. I
have not demonstrated an accuracy, cost, or speed advantage over a closed API;
the concrete goal is an inspectable claim-triage workflow built around Gemma,
with clear limits on what its output establishes.

**PENDING — support the application-specific Gemma discussion with the actual
live receipt before submitting.**

## Prize Categories

**PENDING — Best Use of Gemma is conditional and is not yet claimed.** The
[challenge page](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)
allows Gemma through another provider. Add the category only after the exact
Gemma runtime has a real sanitized receipt; otherwise remove this section.

Final publication checks: **PENDING** personal eligibility and active DEV form;
**PENDING** owner approval of code, sources, originality, and final prose;
**PENDING** genuine demo and public final code link; **PENDING** submission by
October 25, 2026, 11:59 PM PDT (October 26, 2:59 AM EDT). Publish one entry only.
Published DEV URL and timestamp: **PENDING**.
