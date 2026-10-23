# Completion requirements — 2026-10-23

Written before the completion changes. Governing requirements remain issue #1
(SPEC v2), requirements.md R01–R12, design.md, and tasks.md. This document
specifies the missing validation behavior and acceptance checks; it does not
authorize live inference, publication, paid services, or attest to human review.

## Evidence and independent judgment (R04, R05, R09; A3–A5)

- Evidence files are candidate data, including records carrying
  `verified_by_human: true`. That flag alone never authorizes a confident label.
- Validate `claim-evidence/v1`, unique nonempty string IDs, bounded nonempty
  excerpts and source metadata (publisher, title, HTTPS URL, ISO source date).
  Reject malformed data before inference, including programmatic API input.
- Add optional `--review-file` for a separately supplied owner review receipt,
  schema `claim-review/v1`, with `claim`, `verdict`, `evidence_ids`,
  `evidence_sha256`, `reviewed_by`, and `reviewed_on` (ISO date). The reviewer
  explicitly approves one of TRUE/FALSE/MISLEADING for that exact trimmed claim
  and source set after independently checking provenance and entailment.
- `evidence_sha256` is SHA-256 of UTF-8 JSON of the complete supplied evidence
  list sorted by ID, using `sort_keys=True`, `ensure_ascii=False`, and compact
  separators `(',', ':')`. This binds source content and metadata to review.
  A hash binds content, not reviewer identity; supplying a receipt is an
  explicit local trust decision, not cryptographic proof of human review.
- Reject malformed, mismatched, duplicate, stale-content, or empty-source
  receipts before inference. Receipt source IDs must exist in the evidence.
  Never bundle a receipt claiming a human review that has not occurred.
- Without a valid receipt, accept only UNVERIFIABLE. With a valid receipt,
  accept either UNVERIFIABLE or the independently approved verdict, and require
  the confident card to cite exactly the receipt's evidence IDs. Gemma alone
  cannot authorize an assessment of entailment or conflicting evidence.

## Response, network, and input boundaries (R01–R08; A1, A3, A6–A8)

- Require provider metadata model to be exactly the configured `:free` tag;
  absent, nonstring, base-only, repeated-suffix, and different tags fail closed.
- Validate outer response shape and a completed assistant message. Reject
  truncated/refused/tool responses, invalid JSON, duplicate JSON keys,
  nonstandard constants, wrong field types, noncanonical verdicts, extra model
  fields, unknown/duplicate evidence IDs, and unbounded content. Code supplies
  claim/model/disclosure and emits only the seven documented card fields.
- Provider/error content is untrusted. Error output uses fixed sanitized
  messages, never raw model content, provider errors, exception reasons, or
  untrusted metadata. Escape terminal controls in human-readable output while
  preserving literal text in the machine-readable card.
- Bound evidence and response file/body reads. Disable HTTP redirects, retries,
  and provider fallbacks; cap provider input/output prices at zero using the
  documented request controls. Keep one client call per valid claim and the
  fixed HTTPS URL/model/30-second timeout. Invalid claim/evidence/review/key
  makes zero calls. `--claim` takes precedence over stdin; document it.

## Evaluation and handoff (R09–R12; A5, A9–A12)

- Keep eight candidate cases and four intended label categories, but make
  current allowed outcomes explicit: all unreviewed fixtures must abstain.
  Correct the misleading example to contain a material unsupported inference.
- Offline mocks verify validation behavior, not factual accuracy or live model
  execution. Test synthetic reviewed receipts separately and label them as
  synthetic. Print candidate review status, effective allowed outcomes, actual
  result, and request counts; fail on malformed fixtures or mismatches.
- Add adversarial regression tests for the boundaries above. Tests must make
  zero network calls and leave the process environment unchanged.
- Live eval requires both `--live` and explicit `--confirm-free-allowance`, a
  present env key, and at most eight cases. Count attempts, stop after provider
  failure, never retry. An unreviewed abstention must not be advertised as
  verified coverage of TRUE/FALSE/MISLEADING. Missing live prerequisites are
  BLOCKED/nonzero. No live requests are authorized by this local completion run.
- To make the eventual reviewed evaluation runnable without changing code or
  promoting fixture flags, accept optional `--review-dir`: one independently
  created `case-ID.json` receipt per reviewed candidate, each bound to that
  case's supplied evidence subset. Validate all supplied receipts before any
  live attempt, require approved labels to match the candidate's intended
  label, and allow the reviewed label or honest abstention for that case.
  Missing receipts leave those cases explicitly unreviewed. Print reviewed
  coverage separately; an all-abstention result is never four-label accuracy.
- Update README and task status with actual commands/results, accurate agent
  credit, and remaining human gates. Save an A1–A12 local verification receipt,
  a 60–90-second real-run demo checklist, and an unpublished DEV draft with
  explicit placeholders for unavailable live/demo evidence. Never synthesize
  a successful demo, review, API invocation, eligibility, or published entry.
