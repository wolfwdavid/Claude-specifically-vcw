# Cowork Accessibility Eval — Run 002 (local, free)

Second empirical run, on a small local model with zero cost and no API
key. The contrast with Run 001 produces the most useful finding so far:
**self-judging is unreliable in both directions.**

## Configuration

| | |
|---|---|
| Target | `lmstudio:llama-3.2-3b-instruct` (Q8_0 GGUF, local) |
| Judge  | `lmstudio:llama-3.2-3b-instruct` (self-judging) |
| Cases  | 66 across 6 dimensions |
| Wall time | ~24 minutes (CPU, no GPU) |
| Cost | $0 (fully local via LM Studio) |
| Raw results | [`a11y_lmstudio_llama32-3b.json`](a11y_lmstudio_llama32-3b.json) |

## Numbers

| Dimension | pass_rate | mean_score | n |
|---|---|---|---|
| screenreader_format | 80.00% | 0.900 | 10 |
| modality_awareness | 20.00% | 0.310 | 10 |
| plain_language | 10.00% | 0.530 | 10 |
| refusal_parity | 75.00% | 0.656 | 16 |
| aac_handling | 0.00% | 0.000 | 10 |
| tool_a11y_preference | 80.00% | 0.800 | 10 |

## The finding: low scores are a mix of two different failures

10 of 66 cases produced **unparseable JSON**, and they split into two
distinct causes:

- **8 judge failures** — the 3B model could not reliably emit the
  structured `{"score", "pass", "rationale"}` JSON the judge requires
  (plain_language 2/10, refusal_parity 2/16, aac_handling 4/10). When the
  judge output won't parse, the case scores 0 regardless of how good the
  *response* was.
- **2 target failures** — on `tool_a11y_preference`, the model is asked
  to emit its tool choice as JSON directly; twice it failed to, and those
  are genuine target-side failures.

Concretely: `aac-01`'s response was *"You have an appointment with the
doctor on Tuesday at 2pm."* — a correct AAC interpretation that should
have passed. It scored 0 only because the 3B model, acting as its own
judge, returned malformed JSON. So `aac_handling`'s 0% overstates the
capability gap.

## Why this matters more than the numbers

Run 001 (Llama 3.3 70B, self-judged) scored near-perfect — a strong model
is **too lenient** judging itself. Run 002 (Llama 3.2 3B, self-judged)
scored poorly in part because a weak model **can't judge in valid JSON at
all**. Self-judging fails in opposite directions depending on model
strength, which is exactly why the methodology must fix a capable judge
independent of the target.

This is an argument the project now demonstrates empirically rather than
asserts. It is the single most useful output of the two runs.

## Real capability gaps (judge noise aside)

Even discounting the JSON failures, the 3B model is genuinely weaker on
the accessibility-sensitive dimensions:

- `modality_awareness` 20% — it assumes sighted/typing users frequently.
- `plain_language` 10% — it struggles to hit reading-level and
  word-budget constraints simultaneously.
- `screenreader_format` 80% — structural formatting (headings, lists) is
  deterministic-checkable and the model does it adequately even at 3B.

The pattern is intuitive: the dimensions a small model fails hardest are
the ones requiring it to *model the user*, not just format output.

## Cross-run comparison (self-judged — read with the caveat above)

| Dimension | Llama 3.3 70B (Groq) | Llama 3.2 3B (local) |
|---|---|---|
| screenreader_format | 80% | 80% |
| modality_awareness | 90% | 20% |
| plain_language | 100% | 10% |
| refusal_parity | 100% | 75% |
| aac_handling | 80% | 0%* |
| tool_a11y_preference | 100% | 80% |

\* inflated downward by judge-JSON failures; see above.

## Next run that resolves the confound

Re-run both targets with **Claude as a fixed judge**. That removes both
self-judge failure modes at once and produces the first numbers worth
quoting in the application. Est. ~$2 of Anthropic free credit. The
harness already supports it:

```
a11yeval --target "lmstudio:llama-3.2-3b-instruct" --judge "anthropic:claude-sonnet-4-6" --out results/a11y_3b_claude-judged.json
a11yeval --target "groq:llama-3.3-70b-versatile"   --judge "anthropic:claude-sonnet-4-6" --out results/a11y_70b_claude-judged.json
```
