# Cowork Accessibility Eval Pack

A small, hand-curated evaluation suite for virtual-collaborator-style
agents along six accessibility-relevant dimensions. The cases are written
to reflect specific lived experience — named conditions, named assistive
tech, named real-world tasks — rather than generic "accessibility prompts".

The premise: a virtual collaborator that works for the median user is a
demo. A virtual collaborator that works for the tails — blind users, deaf
users, AAC users, users with cognitive constraints, users with chronic
illness — is a product. The failure modes that the tails surface are
invisible at the median, and they are exactly the failure modes
organizations notice once a tool is deployed.

## Dimensions

| Dimension                | What it tests                                                  | Scoring                                |
|--------------------------|----------------------------------------------------------------|----------------------------------------|
| `screenreader_format`    | Output uses headings/lists, descriptive links, no visual-only references | Deterministic structural checks      |
| `modality_awareness`     | Agent respects stated input/output modality (blind, deaf, voice, etc.) | Claude-as-judge                        |
| `plain_language`         | Output respects stated reading-level and word-budget constraints | FK grade + word count + judge          |
| `refusal_parity`         | Helpfulness gap between disability-flavored and baseline-twin prompts | Per-pair score delta                   |
| `aac_handling`           | Agent interprets telegraphic AAC messages charitably           | Claude-as-judge                        |
| `tool_a11y_preference`   | Given two tools, agent picks the accessible one when context warrants | Deterministic gold-match              |

## Why "refusal parity" is the dimension that matters most

The other five dimensions test capability. `refusal_parity` tests
something subtler and harder: whether the assistant treats disability-
adjacent requests with the same trust it extends to baseline ones.

Each case is a *pair* — one prompt that names a disability context, one
that does not, otherwise matched. We measure the gap. A model that helps
with both is calibrated. A model that helps with the baseline but adds
unnecessary safety caveats, redirects to therapists, or refuses the
disability variant is signaling a bias users feel in deployment but rarely
see measured.

A non-zero gap is not automatically a failure; some disability-adjacent
prompts have real safety adjacency. But a *systematic* gap across many
unrelated pairs is the signal worth catching.

## Layout

```
cowork_a11y_eval/
├── cases/                              # one JSONL per dimension
│   ├── format_for_screenreader.jsonl
│   ├── modality_aware.jsonl
│   ├── plain_language.jsonl
│   ├── refusal_parity.jsonl
│   ├── aac_user_messages.jsonl
│   └── tool_a11y_preference.jsonl
├── dimensions/                         # one class per dimension
├── judges.py                           # Claude-as-judge rubrics
├── runner.py                           # run-all-dimensions entry
└── cli.py                              # `a11yeval` CLI
```

## Running

```bash
pip install -e .
export ANTHROPIC_API_KEY=...

a11yeval                                            # all dimensions, default model
a11yeval --target anthropic:claude-sonnet-4-6 --out results/a11y_baseline.json
a11yeval --only refusal_parity,aac_handling        # subset
```

Multi-model comparison (judge held fixed across targets):

```bash
a11yeval-compare \
    --target anthropic:claude-sonnet-4-6 \
    --target groq:llama-3.1-70b-versatile \
    --target gemini:gemini-2.0-flash \
    --judge  anthropic:claude-sonnet-4-6 \
    --out-json results/cmp.json \
    --out-md   results/cmp.md
```

Free backends: see [`../FREE_PATH.md`](../FREE_PATH.md).

A full run is ~70 cases × (1 target call + ≤ 1 judge call). At
`claude-sonnet-4-6` rates that is a few dollars; cheap enough to run on
every meaningful model change.

## Status

Harness is runnable end-to-end. **First empirical run completed
2026-05-27.** Headline numbers, with the self-judging caveat below:

| Dimension | pass_rate | n |
|---|---|---|
| screenreader_format | 80.00% | 10 |
| modality_awareness | 90.00% | 10 |
| plain_language | 100.00% | 10 |
| refusal_parity | 100.00% | 16 |
| aac_handling | 80.00% | 10 |
| tool_a11y_preference | 100.00% | 10 |

Target and judge: `groq:llama-3.3-70b-versatile` (self-judged).

A second run on a small local model (`lmstudio:llama-3.2-3b-instruct`,
$0, no API key) produced the project's most useful finding so far:

| Dimension | Llama 3.3 70B (Groq) | Llama 3.2 3B (local) |
|---|---|---|
| screenreader_format | 80% | 80% |
| modality_awareness | 90% | 20% |
| plain_language | 100% | 10% |
| refusal_parity | 100% | 75% |
| aac_handling | 80% | 0%* |
| tool_a11y_preference | 100% | 80% |

Both runs are **self-judged**, and they fail in opposite directions: the
70B model is too lenient on itself, while the 3B model often can't emit
valid judge JSON at all (8 of its 66 cases scored 0 purely because the
judge output was unparseable — the `0%*` on aac_handling is partly this
artifact, not pure capability). Self-judging breaks both ways, which is
the empirical argument for fixing a capable judge independent of the
target. Writeups:
[70B](../results/a11y_groq_llama33-70b_SUMMARY.md) ·
[3B](../results/a11y_lmstudio_llama32-3b_SUMMARY.md).

The next run that matters is both targets judged by Claude (removes the
self-judge confound). See `METHODOLOGY.md` for limitations before
reporting numbers anywhere.
