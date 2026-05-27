# Next Experiments

The harness is runnable end-to-end. These are the experiments that turn
`RESEARCH_NOTE.md`'s **RESULTS PENDING** tables into measured numbers.
Each item below is sized to a single Torch session.

## E1 — Smoke test on the seed benchmark (1 hour)

Goal: verify the full pipeline runs against the real 100K registry and the
numbers are sane before scaling up.

```bash
trbench export-registry --root .../hugginface_profile/ai_tools --out data/registry.jsonl
trbench retrieve --registry data/registry.jsonl --retriever bm25 --k 10 --out results/e1_bm25.json
trbench retrieve --registry data/registry.jsonl --retriever dense --k 10 --out results/e1_dense.json
trbench retrieve --registry data/registry.jsonl --retriever hierarchical --k 10 --out results/e1_hier.json
```

**Stop condition:** all three retrievers produce non-empty hit lists and
at least one of them places the gold tool in the top-10 for ≥ 8/15 seed
tasks. If not, the seed tasks are mis-specified — fix the seed set, not
the retrievers.

## E2 — Generate the 500-task benchmark (2–4 hours)

Goal: scale the benchmark to a size where retriever differences are
statistically distinguishable.

- Write `scripts/generate_benchmark.py`: for each capability bucket, draw
  5–10 tools, prompt `claude-sonnet-4-6` for 2–3 natural-language queries
  that point unambiguously at the tool, and write to `data/candidates.jsonl`.
- Hand-review every candidate. Reject any whose query also matches a
  sibling tool. This is the unglamorous step that decides whether the
  benchmark is honest.
- Final benchmark lands in `data/tasks.jsonl`.

**Stop condition:** ≥ 500 tasks, with inter-bucket coverage no worse than
3:1 between the most- and least-represented buckets.

## E3 — Retrieval sweep (4–6 hours, mostly GPU)

```bash
for r in bm25 dense hierarchical; do
  for k in 5 10 20 50; do
    trbench retrieve --registry data/registry.jsonl --tasks data/tasks.jsonl \
      --retriever $r --k $k --out results/e3_${r}_k${k}.json
  done
done
```

Hierarchical also sweeps `bucket_top_n ∈ {1, 3, 5, 10}` — edit the
constructor or expose it through the CLI.

**Stop condition:** retrieval recall@10 for dense and hierarchical is
≥ 0.85, *or* a clear analysis of why it isn't.

## E4 — Agent-in-the-loop runs (overnight)

```bash
for r in bm25 dense hierarchical; do
  trbench agent --registry data/registry.jsonl --tasks data/tasks.jsonl \
    --retriever $r --k 20 --model claude-sonnet-4-6 \
    --out results/e4_${r}.json
done
```

**Stop condition:** agent accuracy reported per retriever, with a
confidence interval (bootstrap over the 500 tasks).

## E5 — Abstention probe (1 evening)

Build `data/tasks_held_out.jsonl`: a copy of `data/tasks.jsonl` with 20%
of the gold tools surgically removed from the registry. The agent should
return `tool_id = -1` on those tasks. Report abstention precision and
recall.

## Reporting

After E4 and E5, fill in the result tables in `RESEARCH_NOTE.md`. Keep the
limitations section honest. If hierarchical narrowing closes the gap with
full dense retrieval, that is the headline finding. If it doesn't, the
honest negative result is more valuable than a forced positive one —
write that up explicitly and move toward learned routing.
