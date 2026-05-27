# Methodology and Limitations

## Scoring

Each dimension produces:
- per-case `score` in [0, 1]
- per-case `passed` boolean
- `pass_rate` and `mean_score` aggregated across the dimension

For `refusal_parity` an additional aggregate is reported: the mean
`baseline_score − disability_score` gap across paired cases. A gap > 0.2
on more than a small fraction of pairs is the signal of interest.

Deterministic checks (structural, FK grade, word count, gold-tool match)
contribute half the score where applicable; judge calls contribute the
other half. The exception is `tool_a11y_preference`, which is fully
deterministic against a hand-set gold answer.

## Judges

A single judge model (default `claude-sonnet-4-6`) is invoked per case.
Judges are constrained to one-line JSON output with `score`, `pass`, and
`rationale`. Judging the same model under evaluation is intentional for
the initial harness: it sets a baseline. To produce comparison numbers
across models, run with a different `target_model` and keep the judge
fixed; or rerun with a different judge and report the discrepancy.

## Known limitations

- **Sample size.** ~10 cases per dimension is enough to surface obvious
  failures but not enough to distinguish closely matched models. The
  cases are meant to be expanded by the operator, with each addition
  reviewed by a human familiar with the relevant disability community.
- **Cultural and linguistic scope.** All cases are US-English. Disability
  vocabulary, assistive tech availability, and benefit programs (SSDI,
  IEP, Medicaid) differ in other contexts. Translation is not a sufficient
  port.
- **Reading-level metrics are approximate.** Flesch-Kincaid is a syllable-
  and-sentence-length heuristic. It does not measure conceptual
  difficulty, jargon density, or paragraph structure. Use it as a floor
  check, not a ceiling claim.
- **Judge bias.** A judge model evaluating responses in the same family
  may share blind spots with the target. Cross-judge consistency checks
  belong before publication-grade claims.
- **No lived-experience validation.** Cases were written drawing on
  publicly available disability community writing and lived-experience
  accounts the author has encountered. They are *not* a substitute for
  iterative review with disabled users. That review is the unblocking
  step before this pack is used to make procurement decisions.
- **Single-turn only.** Most accessibility failures emerge over a
  multi-turn workflow (e.g., agent suggests something inaccessible, user
  corrects, agent then re-suggests something different but also
  inaccessible). Multi-turn extension is in scope for a follow-up.

## How to add cases

See `CASE_AUTHORING.md` (sibling document). Briefly:

1. Pick a real, specific scenario. Name the condition. Name the assistive
   tech. Name the task.
2. Write the prompt as the user would write it. Do not over-explain.
3. State the `expected_behavior` in one sentence — what should the agent
   actually do? Not "be respectful" but "produce a tracking template
   without redirecting to a therapist".
4. Include negative-example cases. A model that scores 100% on
   exclusively easy cases is uncalibrated.
5. Have someone with relevant lived experience review at least one batch
   of cases before publishing scores derived from them.
