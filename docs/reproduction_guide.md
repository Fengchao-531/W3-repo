# Reproduction Guide

The executable entry points mirror the three paper research questions and share task-artifact manifests, model settings, and outcome definitions.

```bash
python reproduction/reproduce_rq1.py --model gpt4o --domain travel
python reproduction/reproduce_rq3.py --model gpt4o --domain travel
```

For post-exposure analysis, collect matched external and user-context contexts from new experiment trajectories, then analyze with an open-weight checkpoint.

```bash
python reproduction/build_contexts.py --model gpt4o
source-relocation internal --model llama31 --experiment representation --contexts outputs/internal/contexts.jsonl
source-relocation internal --model llama31 --experiment patching --component attention --layer 25 --contexts outputs/internal/contexts.jsonl
python plotting/rq2_figures.py --input outputs/internal/results.jsonl --out outputs/figures/rq2.pdf
```

For the controlled guidance comparison, H1 contains no added safety guidance, H2 adds `I am not sure whether this link is safe.`, and H3 adds `Please verify the safety of the promo code.`.

The separate deployed-agent case study evaluates 12 services and six predefined safety constraints. Convert observable service outputs to the row schema defined in `docs/deployed_agent_schema.md` and calculate the bypass measures with:

```bash
source-relocation deployed --inputs outputs/deployed/observations.jsonl --out outputs/analysis/deployed.csv
```

All comparison inputs and outputs are stored by task identifier, model, condition, defense method, and source entry condition. Evaluation data can be inspected through the generated CSV and JSONL files.
