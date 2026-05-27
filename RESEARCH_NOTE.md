# Tool Retrieval at 100K Scale: An Empirical Study

**Status:** Draft. Methods and harness implemented; empirical results
pending the full sweep on the NYU Torch HPC cluster. Tables marked
**RESULTS PENDING** will be filled with measured numbers after the
experiments listed in `NEXT_EXPERIMENTS.md` complete.

## 1. Question

A virtual collaborator deployed inside a real organization is exposed to
far more tools than fit in any single context window. Internal APIs,
plug-ins, scripts, and dashboards routinely number in the thousands, and
the trend line is up. The agent's central retrieval problem is no longer
*"which passage answers this question"* but *"which capability, drawn from
a catalog the agent cannot enumerate, executes this user intent."*

This note asks three concrete questions over a 100,000-entry tool
registry:

1. How much of the agent's final task accuracy is determined by the
   retriever versus the model?
2. Does hierarchical taxonomy-walk retrieval recover the quality of full
   dense retrieval while reading a small fraction of the embeddings?
3. How well does the agent abstain when the gold tool is *not* in the
   retrieved shortlist?

## 2. Setup

**Corpus.** 100,020 tool packages, each named `<id>_<slug>` and clustered
into coarse capability buckets by ID-prefix range. Tool descriptions are
short — a slug-derived display name plus the package's `__init__.py`
docstring where present. See `data/README.md`.

**Tasks.** A seed set of 15 hand-curated `(natural-language query,
gold_tool_id)` pairs ships in `tool_retrieval_100k/benchmark.py`. The
larger benchmark (target: 500–1000 tasks) is drafted by Claude and then
human-reviewed; the generator script is the immediate next deliverable.
Task coverage is stratified across capability buckets so the benchmark
does not over-index on any single domain.

**Retrievers compared.**

| Retriever      | Mechanism                                                      |
|----------------|----------------------------------------------------------------|
| BM25           | Tokenize on alphanumeric boundaries; `rank-bm25` over the full corpus. |
| Dense          | `sentence-transformers/all-MiniLM-L6-v2` embeddings; cosine over the full 100K matrix. |
| Hierarchical   | Cluster centroids by ID-prefix bucket; pick top-N buckets, then dense-rerank within. |

**Agent.** `claude-sonnet-4-6` with a structured JSON-output system prompt;
sees the retriever's top-`k` and returns a single selected tool ID or
abstains. See `tool_retrieval_100k/agent/claude_runner.py`.

**Metrics.**
- *Retrieval:* recall@1, recall@5, recall@10, MRR.
- *Agent:* end-to-end accuracy (selected ID == gold ID), abstention
  precision/recall on tasks deliberately stripped of their gold tool.
- *Cost:* embeddings read per query (hierarchical's advantage) and tokens
  consumed (agent's cost ceiling).

## 3. Results

### 3.1 Retrieval-only

**RESULTS PENDING.** Sweep planned for hierarchical with `bucket_top_n ∈
{1,3,5,10}`.

| Retriever     | recall@1 | recall@5 | recall@10 | MRR  | Embeddings read / query |
|---------------|----------|----------|-----------|------|--------------------------|
| BM25          | —        | —        | —         | —    | 0                        |
| Dense         | —        | —        | —         | —    | 100,020                  |
| Hierarchical  | —        | —        | —         | —    | < 5,000 (target)         |

### 3.2 Agent-in-the-loop accuracy

**RESULTS PENDING.** Each retriever's top-`k` shortlist fed to
`claude-sonnet-4-6`; full row-level outputs persisted to
`results/run_<id>.json`.

| Retriever     | k=5   | k=10  | k=20  | k=50  |
|---------------|-------|-------|-------|-------|
| BM25          | —     | —     | —     | —     |
| Dense         | —     | —     | —     | —     |
| Hierarchical  | —     | —     | —     | —     |

### 3.3 Abstention

**RESULTS PENDING.** A held-out 20% of tasks will have their gold tool
removed from the registry; the agent should return `tool_id = -1`. We
report abstention precision and recall.

## 4. Limitations

- The corpus is a generated taxonomy, not a hand-built tool catalog. Its
  semantic density per cluster is lower than a real organization's
  catalog. Results should be read as an upper bound on retrieval
  difficulty per unit of catalog size, not a lower bound on capability
  diversity per unit.
- The agent prompt is intentionally minimal. Production tool-selection
  prompts would include user history, prior tool calls, and confidence
  calibration scaffolding. Excluded here so the signal isolates retrieval
  quality.
- A single embedding model is tested. The recommendation is to swap in
  larger embedders only if the cheaper baseline fails to clear an agreed
  bar; this avoids the common failure mode of attributing improvements to
  the wrong layer of the stack.
- No tool execution is performed. Selection ≠ execution; this benchmark is
  upstream of the side-effect question.

## 5. What this is good for

If hierarchical narrowing closes most of the gap with full-catalog dense
retrieval — the hypothesis under test — that has direct implications for
how Cowork-style agents should be architected: index once at the cluster
level, dense-rerank within a tight window, and spend the saved compute on
the model's actual decision. Conversely, if it doesn't, that's a signal
that capability clustering by namespace is not the right structural prior
for tool retrieval, and the work moves toward learned routing or richer
tool descriptions.

The empirical question is the one worth answering. The harness is in
place; running it is the next step.
