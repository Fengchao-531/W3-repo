# Tricking Agents into Accepting Malicious Information

Reproduction toolkit for the AAMAS 2027 study of source relocation in LLM-based agents. The implementation organizes controlled AgentDojo evaluations, artifact placement, model analysis, defenses, safety guidance, and deployed-agent outcome analysis around RQ1, RQ2, and RQ3.

## Installation

```bash
conda env create -f environment.yml
conda activate source-relocation
pip install -e '.[agent,internal,test]'
```

## Dataset and Experimental Conditions

```bash
source-relocation build --domain travel --manifest outputs/manifests/travel.jsonl
source-relocation run --rq rq1 --experiment relocation --model gpt4o
source-relocation run --rq rq1 --experiment position --model gpt4o
source-relocation run --rq rq1 --experiment preference --model gpt4o
source-relocation run --rq rq1 --experiment instruction --model gpt4o
source-relocation run --rq rq1 --experiment reliability --model gpt4o
source-relocation run --rq rq1 --experiment source_label --model gpt4o
```

## Model Analysis and Safeguards

```bash
python reproduction/build_contexts.py --model gpt4o
source-relocation internal --experiment representation --model llama31 --contexts outputs/internal/contexts.jsonl
source-relocation run --rq rq3 --experiment verification --model gpt4o
source-relocation run --rq rq3 --experiment defenses --model gpt4o --defense datasentinel
source-relocation analyze
```

For defense implementation sources, setup, and run commands, see [RQ3 defense integration](docs/upstream_defenses.md).

## Documentation

Detailed protocols are provided in `docs/installation.md`, `docs/experimental_setup.md`, `docs/model_configuration.md`, `docs/evaluation_metrics.md`, `docs/reproduction_guide.md`, and `docs/figures_and_tables.md`.

Generated datasets, local task trajectories, model-internal activations, figure exports, and statistics are stored in `outputs/` and excluded from version control.
