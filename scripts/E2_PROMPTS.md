# E2 drafting & review prompts

The E2 benchmark queries are drafted and reviewed by Claude model sessions.
These are the exact instructions given to each stage, kept in-repo so the
benchmark's provenance is auditable. `generate_benchmark.py sample` produces
the drafting inputs; `generate_benchmark.py assemble` consumes the reviewed
outputs.

## Stage 2 — drafting prompt (per tool batch)

> You are writing benchmark queries for a tool-retrieval study. For each
> tool below you get its numeric id, its slug, and the slugs of its
> nearest-id sibling tools. Write exactly `queries_wanted` natural-language
> user requests that this tool — and only this tool — would satisfy.
>
> Hard rules:
> 1. A real user voice: first person, describing a need, not naming a tool.
> 2. Do not reuse the slug's words verbatim where a natural synonym exists.
>    At most one content word may be shared with the slug.
> 3. The query must distinguish the tool from every sibling slug shown.
>    Siblings usually differ by role (tracker vs classifier vs simulator):
>    your phrasing must make the intended role unmistakable — e.g. "keep a
>    running log of X over time" (tracker), "tell me which category X falls
>    into" (classifier), "model what would happen if X" (simulator).
> 4. Vary register and length across the queries for one tool (terse,
>    conversational, detailed).
>
> Output JSONL, one row per query:
> {"query": "...", "gold_tool_id": <id>, "source": "e2_generated"}

## Stage 3 — review prompt (per candidate batch, fresh session)

> You are auditing benchmark queries for a tool-retrieval study. For each
> candidate you get the query, the gold tool's slug, and the sibling slugs.
> Judge only one thing: if a competent human librarian were handed this
> query and the full slug list, would they pick the gold tool without
> hesitation?
>
> Reject if:
> - the query plausibly matches a sibling as well as the gold ("ambiguous")
> - the query is unnatural or reads like a slug paraphrase ("unnatural")
> - the query's role signal contradicts the gold slug's role suffix
>   ("wrong-role")
>
> Output JSONL, one row per candidate, copying the input row plus:
> {"verdict": "accept" | "reject", "reject_reason": "<tag or empty>"}

## Provenance note

Drafting and review use separate model sessions with no shared context, so
the reviewer cannot rubber-stamp its own drafts. This replaces the
"hand-review every candidate" step in NEXT_EXPERIMENTS.md with a
model-cross-review; a human spot-check of a random 10% sample is the
recommended follow-up before publishing conclusions that lean on absolute
(rather than relative) retriever numbers.
