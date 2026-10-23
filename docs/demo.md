# Real-run screen demo checklist

Status: **NOT RECORDED. Live Gemma and independent source review are pending.**
This is a recording plan, not evidence that any command succeeded. It follows
R11 and the [completion requirements](../specs/claim-checker-local/completion.md).
No live calls were authorized or made by the local completion run.

## Before recording

- [ ] Read the [A1–A12 verification receipt](verification-2026-10-23.md) and resolve
  its remaining release gates. Have the owner review the code, evidence,
  originality, privacy disclosure, and exact recorded revision.
- [ ] Confirm the account's free allowance and exact
  `google/gemma-4-26b-a4b-it:free` route locally. Public model listings are not
  proof of account access. Configure the environment key outside the recording;
  never display the key, environment dump, headers, account page, or shell history.
- [ ] Independently review a safe public claim and the actual source text. Save a
  valid local `claim-review/v1` receipt bound to the complete evidence list. The
  README's placeholder receipt and test-only synthetic receipts are unusable as
  review evidence. Do not describe the candidate corpus as human reviewed.
- [ ] Complete the separately authorized live sample and at-most-eight-case live
  evaluation. Save sanitized real outcomes, attempt counts, exact observed model
  metadata, and dates. For independently reviewed evaluation cases, use
  `--review-dir /path/to/local-reviews` with `case-01.json` and other actual case
  receipts. Each digest binds only that case's evidence subset; all supplied
  receipts must pass validation before any live attempt. Missing receipts leave
  cases unreviewed. See the [README workflow](../README.md#opt-in-live-evaluation).
  Do not convert mock outputs into a live receipt.
- [ ] Obtain authorization and free allowance for the **two additional live
  requests** in the proposed recording. Account-wide allowance includes prior
  samples, evaluations, and any failed attempts. Do not retry a failed take with
  more inference requests without checking the remaining allowance.
- [ ] Use a clean terminal with only public claims, local test results, and the
  project README visible. Ensure the source/review file paths are suitable for
  display. Run the offline checks on the revision that will be shown.

## Proposed 60–90-second sequence

Keep commands and outputs readable. Silent screen capture is sufficient;
captions are optional. Let each real response finish. If latency pushes the take
past 90 seconds, shorten explanations rather than manufacturing a faster result.

| Approximate time | On screen | What it establishes |
|---|---|---|
| 0–10 seconds | README introduction and current status | Python CLI, remote Gemma inference, provisional cards |
| 10–35 seconds | Run the independently reviewed public claim with `--evidence-file` and its real `--review-file` | Actual source-bound result, evidence IDs, rationale, and disclosure; Gemma may still abstain |
| 35–55 seconds | Run a different public claim without evidence | A real `UNVERIFIABLE` card, or honestly visible validation failure |
| 55–75 seconds | Run `python3 evals/run_eval.py` and show its actual summary | Offline validation and unreviewed candidates' effective abstention outcomes; label this **MOCK / OFFLINE** |
| 75–90 seconds | Show the sanitized live receipt and model identifier, then the privacy/limitations paragraph | Exact observed provider metadata, actual live request counts, and remote inference limitation |

Example recording commands, **only after the prerequisites above are satisfied**:

```bash
python3 claimcheck.py --claim "Earth is the third planet from the Sun." \
  --evidence-file evals/evidence.json --review-file /path/to/local-review.json

python3 claimcheck.py --claim "An unnamed deep-sea species was discovered yesterday."

python3 evals/run_eval.py
```

The first command is suitable only if that exact claim, the actual evidence file,
and the corresponding receipt have truly been independently reviewed. It is not
a shortcut to approving the bundled candidate sources. Avoid the medical
candidate in a short demo. This CLI command supplies the whole evidence file,
so its review digest binds that whole list. Do not reuse a per-case evaluation
receipt unless the supplied evidence list is exactly the same subset.

If the provider fails, the CLI rejects metadata, or the reviewed case abstains,
retain the real outcome. A failure is not a successful demo of Gemma inference;
an abstention is not a verified TRUE/FALSE/MISLEADING example. Resolve the actual
cause and record a later authorized run; do not splice in synthetic verdicts.

## After recording

- [ ] Watch the entire capture for secrets and inaccurate captions. Confirm the
  claims, citations, model, and outputs match the saved real-run receipts.
- [ ] Record the actual duration, capture date, Git revision, request count, and
  final video URL below. Keep the demo unpublished until the owner approves it.
- [ ] Replace the conspicuous demo/live placeholders in the
  [DEV draft](dev-submission-draft.md) with real links and results.

Recording receipt: **PENDING**. Video URL: **PENDING**. Duration: **PENDING**.
Capture date/revision: **PENDING**. Inference attempts during recording:
**PENDING**. Owner approval: **PENDING**.
