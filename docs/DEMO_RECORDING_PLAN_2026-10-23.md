# Claim Checker — 60–90-second contest demo filming script

**Updated October 23, 2026 after the first genuine Gemma 4 26B inference.**

**Observed proof:** On Mac at tested code `6e0c2d5`, compilation completed, offline mocks **23/23** passed, Python unittests **34/34** passed, and Google-hosted `gemma-4-26b-a4b-it` returned a real validated JSON card: `UNVERIFIABLE` with no evidence. [Exact sanitized receipt](LIVE_GEMMA_RECEIPT_2026-10-23.md). The live functionality gate is cleared; **screen recording is not yet evidenced**. The tests do not certify independent factual accuracy. Never show private keys, accounts, sensitive claims or paid billing details.

## Prepare once, before starting screen recording

1. Open Terminal in `~/claim-checker-local` with large text, hide notifications and other windows. Check out `audit/release-hardening-2026-10-22`. Pull the current branch if not already current; documentation-only commits after `6e0c2d5` do not change model behavior.
2. Confirm your **Google AI Studio project is free-tier** and review actual past request usage/cost. Google's published free token price is **not** an account-specific charge receipt.
3. To film a **fresh call**, privately enter and export the key **before recording**, not during the video:

```bash
read -rs "GEMINI_API_KEY?Google AI Studio key (hidden): "
echo
export GEMINI_API_KEY
```

4. Never film a key value, billing info, developer tokens, `env` output, or another person's claim. After the recording, run `unset GEMINI_API_KEY`. The CLI never automatically retries or switches to a paid model.

## Main demo — verbatim narration and actual commands (target 75–90 seconds)

**0:00–0:13 — Title & purpose. Show repository name and terminal. Read:**

> "I built Claim Checker, a Python tool that asks Google's open-weight Gemma model for a quick, provisional assessment of a claim. It's meant to reduce the first round of research, not replace checking the sources."

**0:13–0:40 — Actual live check. Show this command and its real JSON output:**

```bash
python3 claimcheck.py --provider google --model gemma-4-26b-a4b-it --claim "Earth is the third planet from the Sun." --json
```

Read **only if the provider really returns a valid card while filming**:

> "That's a real Gemma 4 response, served through Google's API. Notice the answer is UNVERIFIABLE. The model knows many facts, but because I supplied no independently reviewed evidence, the program refuses to certify this claim as true."

If live access fails while filming, **do not claim a successful fresh inference**. You may instead show the **authentic October 23 recorded terminal receipt** in a clearly titled *previous live run* shot, saying:

> "Here is the actual result captured in my earlier Mac run. This is a recorded Gemma response, not one of the offline mocks."

A prior terminal output is evidence of past runtime success, but challenge judges may prefer a newly recorded working session. Do not substitute a synthetic JSON file as live output.

**0:40–1:04 — Contract tests. Show actual commands/results at recording time:**

```bash
python3 evals/run_eval.py -v
python3 -m unittest discover -s evals -p 'test_*.py' -v
```

Read if actual results match the prior receipt:

> "The mock evaluation passes 23 checks, and the Python regression suite passes 34 tests. Those measure app behavior, including wrong-model and invented-source rejection. They're not a factual-accuracy benchmark."

If actual totals differ, read the **actual** totals, not the historical numbers.

**1:04–1:25 — Tradeoff and limits. Show README's limitations and source rules. Read:**

> "The model runs remotely, so this needs an internet connection. When sources haven't been reviewed, the tool doesn't manufacture citations. The next step would be safe, automatic source collection, but that isn't in this challenge version."

**Optional closing (only if under 90 seconds):**

> "The real benefit is knowing what evidence to find next."

## Record and publish gate

- [x] Actual Mac 23/23 offline mocks, 34/34 unittests, and exact `gemma-4-26b-a4b-it` live JSON result received on Oct 23 at `6e0c2d5`
- [ ] Confirm provider project/usage/cost and account privacy constraints
- [ ] Record and review authentic 60–90s screen demo, edit out credentials/account data; obtain actual video URL
- [ ] Add the video URL to [unpublished DEV article](DEV_WEEK3_SUBMISSION_DRAFT.md), correct any differences from actual footage
- [ ] Verify signed-in DEV Week 3 submission availability, personal eligibility, timing, and article owner approval
- [ ] Publish once, keep resulting public DEV URL and entry receipt
- [ ] Separately approve any merge into `main`; do not make contest publication contingent on falsely marking unreviewed evidence as verified

**Official:** https://dev.to/challenges/hacktoberfest-week3-2026-10-19 . The challenge hub says Week 3 is live while the individual Week 3 page displays "Live Ended"; verify the signed-in entry form rather than assuming either label is conclusive.
