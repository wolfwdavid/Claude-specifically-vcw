# Running this repo for free

Every harness in this repo accepts a backend spec string
(`<provider>:<model>`). Free options below — pick one, set the env var,
go.

## TL;DR — three free paths, ranked

| Path | Cost | Quality ceiling | When to use |
|------|------|-----------------|-------------|
| Ollama on NYU Torch | $0 | Highest (70B+ open weights) | When you have HPC time |
| Groq free tier | $0 | High (Llama 3.1 70B, fast) | When you want speed, no setup |
| Gemini free tier | $0 | Medium-High (2.0-flash) | When you also want a free judge |

## Path 1 — Ollama on Torch (recommended)

One-time setup on the Torch login node (or any machine with the model
weights):

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:70b              # or qwen2.5:72b
ollama serve                          # leave running in a tmux pane
```

Then run the evals:

```bash
a11yeval --target ollama:llama3.1:70b --out results/a11y_llama70b.json
trbench agent --registry data/registry.jsonl --target ollama:llama3.1:70b \
    --retriever hierarchical --out results/tr_llama70b.json
```

The judge still defaults to Claude. To make the judge free too, point it
at Gemini's free tier (see Path 3) or use the same Ollama model:

```bash
a11yeval --target ollama:llama3.1:70b --judge ollama:llama3.1:70b
```

Self-judging is weaker signal but produces a runnable baseline at $0.

## Path 2 — Groq free tier

Sign up at https://console.groq.com, get an API key, export it:

```bash
export GROQ_API_KEY=gsk_...
a11yeval --target groq:llama-3.1-70b-versatile --out results/a11y_groq.json
```

Free-tier rate limits are generous (30 req/min, 6000 req/day at time of
writing). The full a11y eval is ~110 calls — finishes in ~5 minutes.

## Path 3 — Gemini free tier

Sign up at https://aistudio.google.com, create an API key, export it:

```bash
export GOOGLE_API_KEY=AIza...
a11yeval --target gemini:gemini-2.0-flash --judge gemini:gemini-2.0-flash \
    --out results/a11y_gemini.json
```

This is the only fully-free path that uses zero local compute and zero
Anthropic credit — useful when you don't have Torch time and don't want
to claim the $5 Anthropic signup credit yet.

## Mixing free target + paid judge

The judge is where quality matters most. A practical setup: free target,
paid (or free-credit) Claude judge.

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # uses your $5 signup credit
export GROQ_API_KEY=gsk_...

a11yeval --target groq:llama-3.1-70b-versatile \
         --judge anthropic:claude-sonnet-4-6 \
         --out results/a11y_groq_vs_claude_judge.json
```

A full a11y run in this configuration costs $1–2 in judge calls and zero
in target calls.

## Cost reference (rough, change over time)

| Run | Anthropic-only | Free target + Claude judge | All-free |
|-----|----------------|-----------------------------|----------|
| a11y eval (66 cases) | ~$2 | ~$1 (judge only) | $0 |
| tool retrieval E1–E5 | ~$5–10 | ~$2 (judge only) | $0 |

## Getting API keys (signup links)

- Anthropic: https://console.anthropic.com — $5 free credit on signup
- Google AI Studio: https://aistudio.google.com — free tier, no card
- Groq: https://console.groq.com — free tier, no card
- Ollama: https://ollama.com — local only, no account
