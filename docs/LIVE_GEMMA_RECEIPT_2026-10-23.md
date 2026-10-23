# Observed Mac release receipt — first valid live Gemma verdict (October 23, 2026)

**Status:** FIRST LIVE MODEL CARD VERIFIED FROM OWNER-SUPPLIED TERMINAL LOG; technical demo prerequisite cleared, **not** proof of factual accuracy, independent source review, zero cost, final video, acceptance of contest entry, or release/merge authorization.

## Exact tested code and offline results

- Repository: `KyPython/claim-checker-local`
- Checked-out branch: `audit/release-hardening-2026-10-22`
- Tested commit: `6e0c2d5` (terminal `git rev-parse --short HEAD`)
- Environment: owner's macOS Terminal; Python invocation `python3`; actual interpreter version not printed in this particular receipt
- `python3 -m py_compile claimcheck.py evals/run_eval.py evals/test_release_contract.py evals/test_release_gate.py evals/test_provider_routing.py`: completed without reported error
- `python3 evals/run_eval.py -v`: **23/23** offline mock/validation cases passed. These are not live model accuracy measures
- `python3 -m unittest discover -s evals -p 'test_*.py' -v`: **34 tests, all OK**
- GitHub documentation commits made after `6e0c2d5` were **not** part of the tested source tree; no new runtime code changes were made in those documentation commits

## Exactly observed live command

```bash
python3 claimcheck.py --provider google --model gemma-4-26b-a4b-it --claim "Earth is the third planet from the Sun." --json
```

The key was entered with hidden `read -rs`, exported as `GEMINI_API_KEY`, then unset. No key was present in the shared output. The terminal showed a **successful JSON verdict card**, unlike the earlier HTTP 400 and unusable-candidate failures.

### Sanitized, actual returned card

```json
{
  "verdict": "UNVERIFIABLE",
  "rationale": "No evidence was provided to support or contradict the claim.",
  "what_would_settle_it": "Astronomical data or scientific consensus regarding the order of planets in the solar system.",
  "evidence_ids": [],
  "claim": "Earth is the third planet from the Sun.",
  "model": "gemma-4-26b-a4b-it",
  "disclosure": "AI-generated preliminary assessment. Claim text was sent to a remote inference provider. This is not an authoritative fact-check.",
  "provider": "google"
}
```

**Interpretation:** Native Google Gemma generated a card and the CLI's strict model/response/grounding validation passed, returning JSON. `UNVERIFIABLE` is the enforced safe behavior without provided, human-reviewed source evidence, not a statement that Earth is unknown to be the third planet. This verifies one live claim-triage path, **not** eight live golden cases and not independent truth checking.

## Remaining release/contest gates (do not check without receipts)

- [ ] Verify the Google AI Studio project is free-tier eligible, with no attached paid billing surprise; save redacted provider usage for the observed request. Pricing documentation alone does not prove individual cost
- [ ] Review/disambiguate source excerpts and expected labels before asserting evidence-grounded TRUE/FALSE/MISLEADING accuracy; fixtures currently declare `verified_by_human=false`
- [ ] Record/embed authentic 60–90s screen demonstration of a **real** Gemma-generated card (can use this observed output as labeled recorded evidence, not a simulated mock)
- [ ] Confirm owner eligibility, DEV Week 3 signed-in submission access, final article/content and exact entry deadline
- [ ] Obtain final owner approval for GitHub merge and public DEV post; publish only once, record public URL

**Contest:** https://dev.to/challenges/hacktoberfest-week3-2026-10-19 ; **PR:** https://github.com/KyPython/claim-checker-local/pull/2 ; **Issue:** https://github.com/KyPython/claim-checker-local/issues/1 . No inference, keys, subscriptions, CI, merge, deployment or DEV publication was initiated when this receipt was added.
