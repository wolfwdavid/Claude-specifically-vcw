# Claude-specifically-vcw

Research-engineering work on virtual collaborator systems. Two
self-contained projects in this repo:

1. **[`tool_retrieval_100k/`](tool_retrieval_100k/)** — benchmark + research note for
   LLM agent tool retrieval over a 100K-entry catalog. *Below.*
2. **[`cowork_a11y_eval/`](cowork_a11y_eval/)** — hand-curated accessibility eval pack
   for virtual collaborator agents across six dimensions (screen-reader
   format, modality awareness, plain language, refusal parity, AAC
   handling, accessibility-aware tool selection). See
   [`cowork_a11y_eval/README.md`](cowork_a11y_eval/README.md).

Both projects share a pluggable backend layer (`vcw_backends/`) so the
harness runs against Anthropic, Ollama (local), Gemini (free tier), or
Groq (free tier) with a single flag. See [`FREE_PATH.md`](FREE_PATH.md)
to run everything at $0.

---

# Tool Retrieval at 100K Scale

A benchmark and research harness for studying how an LLM agent should
retrieve, rank, and select tools from a catalog far larger than its context
window — the regime that virtual collaborator systems operate in once they
are deployed inside a real organization.

The catalog used here is a 100,000-entry generated tool registry organized
into a coarse taxonomy. The interesting work is not the registry itself; it
is the layer above it. An agent that cannot see all 100,000 tools at once
has to decide what to look at, what to rank, and what to commit to — under
time, token, and reliability constraints.

## Why this exists

Most public retrieval benchmarks evaluate over tens of thousands of
passages, not over a tool surface that an agent will actually act on. The
two settings differ in ways that matter:

- **Tools have side effects.** Picking the wrong passage is a bad answer;
  picking the wrong tool is a bad action.
- **Tools cluster by capability, not topic.** Standard dense retrieval over
  flat catalogs ignores capability structure that agents could exploit.
- **The right answer is often "none of these."** Retrieval recall is not
  enough; calibrated abstention matters.

This harness measures all three.

## What's here

```
tool_retrieval_100k/
├── registry.py            # load a directory of <id>_<slug> tool packages
├── retrievers/
│   ├── bm25.py            # lexical baseline
│   ├── dense.py           # sentence-transformer embeddings + cosine
│   └── hierarchical.py    # taxonomy-walk: pick buckets, then rerank within
├── metrics.py             # recall@k, MRR, agent accuracy
├── benchmark.py           # seed (query, gold_tool_id) tasks + JSONL loader
├── agent/claude_runner.py # Anthropic API agent that selects among hits
└── cli.py                 # `trbench` entry point

tests/                     # smoke tests over a toy registry
RESEARCH_NOTE.md           # write-up draft (results pending)
NEXT_EXPERIMENTS.md        # the experiment plan
```

## Quick start

```bash
pip install -e .
pytest                                            # smoke tests pass on a toy registry

# point the benchmark at a real 100K registry on disk
trbench export-registry --root /path/to/registry --out data/registry.jsonl

# retrieval-only run (no API calls)
trbench retrieve --registry data/registry.jsonl --retriever bm25 --k 10
trbench retrieve --registry data/registry.jsonl --retriever dense --k 10
trbench retrieve --registry data/registry.jsonl --retriever hierarchical --k 10

# full agent-in-the-loop run (requires ANTHROPIC_API_KEY)
trbench agent --registry data/registry.jsonl --retriever hierarchical \
    --k 20 --out results/run_001.json
```

## Status

The harness is runnable end-to-end. The research note's results tables are
intentionally marked **RESULTS PENDING** — they will be filled in after
empirical runs against the full 100,000-entry registry on the NYU Torch
cluster. See `NEXT_EXPERIMENTS.md` for the experiment plan and stop
conditions.

## Why claim 100K?

The on-disk registry is a generated taxonomy of 100,020 tool packages, not
100,000 hand-built tools. That distinction matters and is preserved
throughout this harness: the registry is the *retrieval target*, not the
quality claim. The research question is how an agent navigates a surface
that large, regardless of how the surface was produced.
