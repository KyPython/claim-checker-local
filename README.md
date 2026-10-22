# claim-checker-local

**Status: SPEC v2 approved for implementation handoff; application not yet built or tested.**

A small **Python claim-triage CLI** for the [DEV Hacktoberfest Open-Source AI Challenge, Week 3 — Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19), with the **Best Use of Gemma** category as a conditional entry. The proposed runtime sends a claim to **cloud-hosted open-weight Gemma**, returning an **AI-generated, preliminary** verdict card with honest `UNVERIFIABLE` handling. **It is not a source-grounded, authoritative fact checker without reviewed evidence.**

## Canonical specification

See **[GitHub issue #1 — SPEC v2](https://github.com/KyPython/claim-checker-local/issues/1)** for the complete implementation prompt, architecture, security/privacy conditions, A1–A12 acceptance tests, golden claim evaluation contract, demo requirements and submission gate.

## Required runtime (not yet implemented)

- **Python 3.11+**; no local AI download, no Ollama, no offline model run.
- Fixed model: `google/gemma-4-26b-a4b-it:free` via the OpenRouter HTTPS API, **only if the explicitly free endpoint is available**.
- Maintainer-supplied environment variable `OPENROUTER_API_KEY`. Never commit API keys, enable paid fallback, buy credits or silently use another model.
- End-user input goes to a **remote inference provider**; do not submit secrets, confidential client information or sensitive personal data.
- No deploy, paid CI, analytics, account registration inside the app, background traffic or automatic submissions.

**No functionality, tests, live provider access, cost-zero execution, competition eligibility or completed submission has been demonstrated yet.** README commands and exact test results will be added after implementation, not fabricated in advance.

## Credit and project boundaries

The design adapts the verdict-card format and mandatory `UNVERIFIABLE` outcome from an earlier **private** project, `KyPython/claim-checker` (concept begun October 17, 2026). This is intended to be a **new and distinct** implementation begun October 22 using cloud-served Gemma, during the contest window. Credit significant borrowed work and distinguish coding-agent output from the owner's independently performed work.

## Challenge deadline

Submit **one** post through DEV's Week 3 template with the `#hf26challenge` tag, a working video **or** deployed demo, a code link, open-source AI explanation, and properly attributed build notes by **October 25, 2026, 11:59 PM PDT**. A video may be a **60–90-second demonstration of functionality**, not a coding-process recording. Agent session is optional. Recheck live submission access and human eligibility before publishing.

Changes committed *after* the contest deadline must be identified here if any occur.
