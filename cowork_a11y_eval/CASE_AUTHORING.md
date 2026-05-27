# Case Authoring Guide

Good cases are specific, named, and reflect lived experience. Bad cases
are vague, generic, and inadvertently test that the model knows the word
"accessibility".

## The smell test

A case is good if a person familiar with the relevant disability
community would say *"yes, that's a real situation I've seen agents fail
at"*. A case is bad if it reads like a content brief.

## Template

Each case is a JSON object on a single line of a `.jsonl` file.

```json
{
  "id": "<dim>-<n>",
  "context": "<one line about the user — name the condition and the AT>",
  "prompt": "<the user's actual message — write it as they would write it>",
  "expected_behavior": "<one sentence: what the agent should concretely do>",
  "notes": "<one sentence: why this case exists, the failure mode it tests>"
}
```

Some dimensions add fields (`must_contain_structure`, `must_avoid`,
`fk_grade_max`, `max_words`, `pair_id`, `variant`, `tools`, `gold_tool_id`).
See existing cases in `cases/` for the shape.

## Do

- Name the condition (cerebral palsy, retinitis pigmentosa, ME/CFS, TBI,
  aphasia, Down syndrome). Generic "disability" is weaker signal.
- Name the assistive technology (NVDA, JAWS, ZoomText, Proloquo2Go,
  Dragon, switch input, refreshable braille). It changes what the agent
  should produce.
- Pick a real task (IEP request letter, SSDI form, FAFSA, Medicaid
  paperwork, dating profile, recurring reminder, weekly grocery list).
  Real tasks reveal real failures.
- Vary tone, age, independence level. Don't make every user a
  professional adult; some are 14, some are 70, some live with caregiver
  support and some don't.
- Include cases where the *right* answer is to NOT prefer the
  accessibility-flagged option (the `gold_tool_id: -1` pattern in
  `tool_a11y_preference`). Otherwise the eval just rewards naively
  defaulting to accessible.

## Don't

- Don't write cases that test whether the model knows the names of
  disabilities. That's a trivia eval, not a Cowork eval.
- Don't combine multiple failure modes per case. One disability, one
  task, one expected behavior.
- Don't conflate "should refuse" cases with "should help" cases. The
  refusal-parity dimension exists *because* most disability-adjacent
  prompts are help cases that get mistaken for refusal cases.
- Don't write cases that only the case author can score. If a second
  reviewer cannot apply your `expected_behavior` sentence and produce the
  same pass/fail, the case is too soft.

## When to expand a dimension

Push past 10 cases per dimension once the existing cases consistently
pass; that's when the eval stops discriminating. Add harder, more
specific scenarios. The goal is a pack that produces non-degenerate
scores — not 95% across the board, not 5% across the board.

## Provenance

Note your sources for each case batch. Publicly available disability
community writing is fine. Personal accounts shared in confidence are
not. If you generate candidate cases with an LLM, mark them and
hand-review every one before they enter the JSONL.
