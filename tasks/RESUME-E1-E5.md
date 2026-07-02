# RESUME: E1–E5 run (paused 2026-07-02)

Goal: run NEXT_EXPERIMENTS.md E1–E5 and fill the RESULTS PENDING tables in
`RESEARCH_NOTE.md`. Paused while the registry export was still running.

## Environment facts (verified this session)
- Python 3.11.0, `tool-retrieval-100k` 0.1.0 installed, `trbench` on PATH
- sentence-transformers 5.2.0; MiniLM-L6-v2 downloaded and warm
- **No API keys anywhere** (Anthropic/Groq/Gemini; no .env; no user-scope env
  vars) and no local LM Studio/Ollama server. E2/E4/E5 therefore run through
  Claude Code subagents (`model: sonnet` = claude-sonnet-4-6, the exact model
  RESEARCH_NOTE names) instead of the live `trbench agent` loop.
- Registry ground truth: 100,020 dirs; decade buckets 0–5 hold
  9 / 90 / 900 / 9,000 / 90,000 / 1 tools. Docstrings are templated noise
  ("Rlhf Optimizer (tool #10002)") — slug-derived names carry the signal.
  Bucket-4 siblings differ only by role suffix (tracker/classifier/simulator…),
  so E2 queries must disambiguate the ROLE.

## State at pause
- [x] Registry export DONE: `data/registry.jsonl` = 100,000 tools (the
  corpus's other ~20 dirs don't match `<id>_<slug>` and are correctly
  skipped by the loader). Uncommitted — data/ may be gitignored; check on
  resume, and regenerate with `trbench export-registry` if missing.
- [x] `scripts/generate_benchmark.py` — E2 sample/assemble halves (seed 257,
  quotas 9/40/40/40/40 tools × 3 queries ≈ 507 tasks; sibling context ±6 ids)
- [x] `scripts/E2_PROMPTS.md` — exact drafting + review prompts (provenance)
- [x] `scripts/e3_sweep.py` — 3 retrievers × k∈{5,10,20,50} + hierarchical
  bucket_top_n∈{1,3,5,10}, embeddings-read accounting, → results/e3_summary.json
- [x] `scripts/export_shortlists.py` — E4/E5 bridge stage 1 (batched shortlists,
  golds withheld; `--strip-golds 0.2` for E5)
- [x] `scripts/score_agent_runs.py` — accuracy + bootstrap 95% CI + abstention P/R

## Remaining steps (in order)
1. Confirm `data/registry.jsonl` exists (≈100,020 lines).
2. **E1**: `trbench retrieve --registry data/registry.jsonl --retriever {bm25,dense,hierarchical} --k 10 --out results/e1_{r}.json`
   (first dense call builds the 100K embedding cache — several min on CPU).
   Stop condition: ≥8/15 seed tasks with gold in top-10 on ≥1 retriever.
3. **E2**: `python scripts/generate_benchmark.py sample` →
   subagent drafting per E2_PROMPTS.md (batches of ~40 tools, output
   candidates.jsonl rows) → fresh-session subagent review (verdict rows) →
   `python scripts/generate_benchmark.py assemble` → data/tasks.jsonl.
   Expect max:min bucket ratio ≈4.4:1 (bucket 0 only has 9 tools) — document
   the deviation from the ≤3:1 target in RESEARCH_NOTE limitations.
4. **E3**: `python scripts/e3_sweep.py` (uses data/tasks.jsonl).
5. **E4**: for each retriever: `python scripts/export_shortlists.py
   --retriever {r} --k 20 --out-dir results/shortlists_{r}` → subagents
   (model: sonnet) select per batch using the SYSTEM_PROMPT semantics from
   `tool_retrieval_100k/agent/claude_runner.py` → selections JSONL →
   `python scripts/score_agent_runs.py --shortlists results/shortlists_{r}
   --selections results/selections_{r}.jsonl --out results/e4_{r}.json`
6. **E5**: same bridge with `--strip-golds 0.2` on the best E4 retriever;
   score reports abstention precision/recall.
7. Fill RESEARCH_NOTE.md §3.1/3.2/3.3; restructure table 3.2 to k=20 + CI
   (E4 only runs k=20); update §4 limitations: (a) model-drafted,
   model-cross-reviewed benchmark, human 10% spot-check recommended;
   (b) selection ran via offline batch bridge, not the live API loop;
   (c) bucket-0 coverage skew.
8. Update tasks/todo.md, commit (no AI attribution in messages), push.

## Also owed to David (from the interview thread, answer on resume or now)
- "What questions should I ask?" — expanded client-questions list; a first
  version already exists in
  `hugginface_profile/interveiw/Bishal/interview-prep.md` §C.
