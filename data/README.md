# Data

The benchmark indexes a tool registry — a directory whose immediate children
are tool packages named `<id>_<slug>` (for example `12_text_to_speech` or
`10148_ai_affective_tts`). The loader does not import the tools; it only
reads directory names and optional `DESCRIPTION.md` / `__init__.py`
docstrings.

## Pointing the benchmark at a registry

A pre-built 100,000-entry generated registry lives at
`hugginface_profile/ai_tools/` in a sibling repo. To use it as the corpus:

```bash
trbench export-registry \
    --root /path/to/hugginface_profile/ai_tools \
    --out data/registry.jsonl
```

This produces a flat JSONL snapshot the benchmark can load in a couple of
seconds without re-scanning the filesystem.

## Adding tasks

Hand-curated seed tasks live in `tool_retrieval_100k/benchmark.py`. To run
against a larger task set, write a JSONL file with one task per line:

```json
{"query": "Convert text into spoken audio.", "gold_tool_id": 12, "source": "seed"}
```

`scripts/generate_benchmark.py` (TODO) drafts additional candidates with
Claude and emits them for human review before they enter the JSONL.

## Cache

`data/cache/` holds embedding matrices. Cached files are keyed by model name
and registry fingerprint, so swapping the embedding model or changing the
registry forces a rebuild automatically. The directory is gitignored.
