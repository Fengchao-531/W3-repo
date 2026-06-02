# LLM-Bench

Self-contained prompt-injection benchmark bundle for the `W3` repo.

This directory is organized so it can be pushed to Git, cloned on `csiro`, and run directly without depending on the local `Attack-Methods/` tree.

## Layout

```text
LLM-Bench/
├── datasets/                     # Bundled benchmark inputs
├── result/
│   ├── M3/                       # Completed M3 results to keep in Git
│   └── CSIRO/                    # Auto-created on CSIRO runs (ignored by Git)
├── requirements.txt
├── run_llm_bench.py              # Main benchmark runner
├── run_llm_bench.sh              # Shell wrapper
└── run_gpt5_our_attack_full.py   # Dedicated GPT-5 runner for our_attack_full
```

## Bundled datasets

The benchmark ships with these six JSONL inputs under `datasets/`:

- `agentdojo_travel_1540_combined.jsonl`
- `agentdojo_travel_1540_context_ignoring.jsonl`
- `agentdojo_travel_1540_escape_characters.jsonl`
- `agentdojo_travel_1540_fake_completion.jsonl`
- `agentdojo_travel_1540_naive.jsonl`
- `our_attack_full.jsonl`

`run_llm_bench.py` uses `datasets/` by default and only falls back to `../Attack-Methods/generated/` if a bundled file is missing.

## Models and routing

`run_llm_bench.py` routes models by runtime:

- `M3`: `claude_3_haiku`, `claude_3_5_sonnet`, `gpt_4`, `gpt_5`
- `CSIRO`: `llama_3_1_8b`, `deepseek_v3`

Auto-detection is based on hostname and filesystem, but you can always force it with `--runtime M3` or `--runtime CSIRO`.

## Quick start on CSIRO

1. Create and activate an environment.
2. Install the Python dependencies.
3. Export the local model paths.
4. Run a smoke test first, then the full benchmark.

Example:

```bash
cd W3
python -m venv .venv
source .venv/bin/activate
pip install -r LLM-Bench/requirements.txt

export LLAMA_3_1_8B_MODEL_PATH=/path/to/llama-3.1-8b
export DEEPSEEK_V3_MODEL_PATH=/path/to/deepseek-v3

python LLM-Bench/run_llm_bench.py --runtime CSIRO --show-models
python LLM-Bench/run_llm_bench.py --runtime CSIRO --models llama_3_1_8b --limit-groups 5
python LLM-Bench/run_llm_bench.py --runtime CSIRO --models llama_3_1_8b deepseek_v3 --device cuda:0
```

Results will be written to `LLM-Bench/result/CSIRO/`.

## Quick start on M3

For API-backed runs:

```bash
cd W3
python -m venv .venv
source .venv/bin/activate
pip install -r LLM-Bench/requirements.txt

export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...

python LLM-Bench/run_llm_bench.py --runtime M3 --show-models
python LLM-Bench/run_llm_bench.py --runtime M3 --models gpt_4 gpt_5
python LLM-Bench/run_gpt5_our_attack_full.py --runtime M3
```

Optional model alias overrides:

- `GPT_4_MODEL`
- `GPT_5_MODEL`
- `CLAUDE_3_HAIKU_MODEL`
- `CLAUDE_3_5_SONNET_MODEL`

## Result handling

- `result/M3/` contains the completed M3 benchmark outputs and should be committed.
- `result/CSIRO/` is for CSIRO-side runs and is ignored by Git.
- `result/*/cache/` is transient prompt cache data and is ignored by Git.

## Included M3 results

Current committed M3 outputs include:

- all five AgentDojo baseline attack sets
- `our_attack_full.jsonl`
- `gpt5_our_attack_full.jsonl`
- `summary.json`

The committed summary has been aligned with the dedicated GPT-5 `our_attack_full` run so the numbers are consistent.
