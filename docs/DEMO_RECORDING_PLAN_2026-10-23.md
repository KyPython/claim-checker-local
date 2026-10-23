# Claim Checker — reviewed, verbatim contest filming script

**Reviewed October 23, 2026 — recording target: 75–90 seconds.** This is a filming runbook, not evidence that a video was recorded or a DEV entry published.

## Verified facts and scope

At tested **code commit `6e0c2d5`** on the owner's Mac, Python compilation succeeded, the **offline deterministic/validation suite passed 23/23**, and the **unit suite passed 34/34**. One real Google-hosted `gemma-4-26b-a4b-it` call returned a contract-valid JSON card with `verdict=UNVERIFIABLE` and `evidence_ids=[]`. [Actual sanitized receipt](https://github.com/KyPython/claim-checker-local/blob/audit/release-hardening-2026-10-22/docs/LIVE_GEMMA_RECEIPT_2026-10-23.md).

**What this proves:** one real Gemma-backed, no-source abstention path plus local software checks. It does **not** prove accurate TRUE/FALSE fact-checking, an eight-case live accuracy score, independent review of the other source fixtures, actual $0 usage, or measured time savings.

**Who wrote what:** The original Python implementation was AI-authored using a coding agent. The user directed the project and ran the Mac tests. Do not imply that the user personally wrote all the code. The [DEV draft](https://github.com/KyPython/claim-checker-local/blob/audit/release-hardening-2026-10-22/docs/DEV_WEEK3_SUBMISSION_DRAFT.md) contains the fuller attribution.

## Before recording (off camera)

1. **Prepare Terminal.** Open a fresh Terminal window, enlarge text, disable notifications and close windows with personal data. Run:

```bash
cd "$HOME/claim-checker-local"
git switch audit/release-hardening-2026-10-22
git pull --ff-only
python3 -m py_compile claimcheck.py evals/run_eval.py evals/test_release_contract.py evals/test_release_gate.py evals/test_provider_routing.py
python3 evals/run_eval.py -v
python3 -m unittest discover -s evals -p 'test_*.py' -v
```

**Stop if a check fails.** If code changes from the tested version, do not carry forward the earlier 23/34 pass counts without rechecking. Documentation-only changes do not establish a new code test receipt.

2. **Check the account.** Confirm in Google AI Studio that the selected project uses an eligible free tier and inspect usage for the earlier call. Google's advertised free price is not evidence of this particular account's charges. Use only a public, non-sensitive test claim.

3. **Set the key privately, with screen recording OFF.** Do not paste an API key into the video, chat, history, or project files:

```bash
read -rs "GEMINI_API_KEY?Google AI Studio key (hidden): "
echo
export GEMINI_API_KEY
clear
```

4. **Start the recording.** On macOS, press **Shift–Command–5**, choose **Record Selected Portion**, select the Terminal region, use **Options → Microphone** to select your microphone, then **Record**. Keep the screen readable and never reveal a key, account identifier, or private information.

5. **Keep two proof types distinct:** a live model result and an offline test summary. The video may pause for provider latency; the approximate timestamps are editing targets, not promises about API speed.

## Say this aloud — one main take

### 0:00–0:15 — What this is

**On screen:** Terminal and repository name. **Read verbatim:**

> "This is Claim Checker, a Python prototype I directed and tested with coding-agent help. It asks Google's open-weight Gemma model for a first-pass assessment of a claim."

### 0:15–0:49 — Show actual Gemma output

**On screen:** Run this **one live call**. It may take longer than expected; don't automatically retry and don't replace its output with a fabricated example.

```bash
python3 claimcheck.py --provider google --model gemma-4-26b-a4b-it --claim "Earth is the third planet from the Sun." --json
```

**Only if a real JSON card appears:** point to `verdict`, `evidence_ids`, and `what_would_settle_it`. **Read:**

> "I chose an obvious claim on purpose. Gemma returns UNVERIFIABLE because I didn't give it reviewed sources. The useful part is 'what would settle it'—a suggestion for the kind of evidence to find next. It's a starting point, not a fact-check."

The specific wording in `what_would_settle_it` may change on another run. Show what the model *actually* returned; don't read invented quotes or assert a different verdict.

### 0:49–1:10 — Demonstrate the safeguards

**On screen:** Show brief **actual** test summaries, not dozens of scrolling lines. These are offline tests:

```bash
python3 evals/run_eval.py | tail -n 9
python3 -m unittest discover -s evals -p 'test_*.py' -q
```

**Only if the current results pass as expected, read:**

> "I got 23 passing mock and validation checks and 34 passing unit tests. They test things like fake source IDs and the wrong model. They don't measure real-world fact-checking accuracy."

If results differ, state the **actual** counts and preserve any failure; do not edit the footage to imply a pass.

### 1:10–1:30 — Open-weight benefit, limits and finish

**On screen:** Leave the card visible; briefly point to the model and disclosure fields. **Read:**

> "Gemma is open-weight, but this demo uses Google's hosted API, so it needs internet and sends the claim to Google. It doesn't collect or verify sources automatically, and I haven't measured time saved. It does tell me what to check next."

## If the live call fails while filming

**Do not say that the fresh call succeeded.** Stop filming or label a separate **“Earlier successful run — October 23”** shot with the [authentic terminal receipt](https://github.com/KyPython/claim-checker-local/blob/audit/release-hardening-2026-10-22/docs/LIVE_GEMMA_RECEIPT_2026-10-23.md). Exact fallback narration:

> "This attempt didn't return a usable card. Here is the successful Gemma response captured from an earlier Mac run, separate from the offline test fixtures."

A displayed earlier terminal log is not the same as an on-camera live request. Do not imply that it meets every possible judge's demo expectation. No paid fallback or unattended retry.

## After recording

1. Stop recording with the macOS menu bar control. **Off camera**, run `unset GEMINI_API_KEY` and close the session.
2. Watch the entire clip. Check that all spoken claims match visible results; edit out credentials or private account screens. If the call stalls, edit for length **without** presenting a historical result as if live.
3. Save the final video link in the [unpublished DEV draft](https://github.com/KyPython/claim-checker-local/blob/audit/release-hardening-2026-10-22/docs/DEV_WEEK3_SUBMISSION_DRAFT.md). Confirm signed-in contest submission access before publication.

## Release checklist — evidence only

- [x] Mac compiled; 23/23 offline checks and 34/34 unit tests passed at `6e0c2d5`
- [x] A true Google Gemma 4 26B response passed app validation and returned no-source `UNVERIFIABLE`
- [ ] Account/project free-tier eligibility and **actual usage/cost** independently reviewed
- [ ] Actual screen-recording completed, inspected and linked
- [ ] Signed-in DEV Week 3 entry access and eligibility confirmed
- [ ] Owner reviews and approves article and submits once; resulting DEV URL recorded
- [ ] Any `main` merge approved and separately verified
- [ ] Source-fixture review / factual accuracy stays **unverified** until independently assessed

**Official competition page:** https://dev.to/challenges/hacktoberfest-week3-2026-10-19 . It lists the October 25 submission date and permits Gemma served by another provider. The page currently shows “Live Ended,” so actual signed-in submission availability must be checked; the recording script cannot resolve that status.

**Editorial review coverage:** Notion source/provenance check; Compound Engineering coherence, feasibility and security *principles* (not an independent subagent panel); Compound Writing developmental edit, first-time viewer read, line edit, AI-residue pass, and final-pass check. Spoken words were tightened without changing observed facts.
