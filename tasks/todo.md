# E1–E5 Execution — fill RESEARCH_NOTE.md tables

Constraint discovered at start: no API keys (Anthropic/Groq/Gemini) and no local
LLM server available. Adaptation: E1/E3 run fully local; E2/E4/E5 use Claude
Sonnet 4.6 through a batched selection bridge instead of the `trbench agent`
live loop. Documented in RESEARCH_NOTE limitations.

## Plan
- [ ] Inspect registry semantic structure (bucket populations, description quality)
- [ ] E1 — export registry.jsonl; bm25/dense/hierarchical @ k=10 on 15 seed tasks; check stop condition (≥8/15 top-10)
- [ ] E2 — scripts/generate_benchmark.py: stratified tool sample → model-drafted queries → ambiguity review → data/tasks.jsonl (target ≥500, ≤3:1 bucket skew)
- [ ] E3 — retrieval sweep: 3 retrievers × k∈{5,10,20,50}; hierarchical bucket_top_n∈{1,3,5,10}; embeddings-read accounting
- [ ] E4 — agent-in-the-loop @ k=20, all 3 retrievers, claude-sonnet-4-6 via batch bridge; bootstrap 95% CI
- [ ] E5 — abstention probe: 20% golds stripped from registry; abstention precision/recall
- [ ] Fill RESEARCH_NOTE.md §3 tables; update §4 limitations (model-reviewed benchmark, bridge methodology)
- [ ] Commit results + note

## Review
(to fill on completion)
