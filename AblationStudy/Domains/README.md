# Cross-Domain Ablation

This folder implements the W3 cross-domain ablation scaffold for `banking`, `slack`, and `workspace`.

Default design:

```text
domains = banking, slack, workspace
benchmark_version = v1.2.2
selected tasks/domain = 10
desires/task = 3
carriers/desire = 3
instances/domain = 90
Exp1 runs/domain = 90 * 3 = 270
Safety Exp2 new runs/domain = 90 * 2 = 180
total new model runs = 1350
```

The generated Exp2 safety queue never contains H1. H1 is defined as the same-domain Exp1 `UC-M` run:

```text
H1 = <domain_instance_id>_UCM
H2 = H1 + concern sentence
H3 = H2 + explicit verification sentence
```

Build everything up to validated manifests and queues:

```bash
./07_build_all.sh
```

Run the full ablation and then regenerate processed tables, statistics, and figures:

```bash
export OPENAI_API_KEY="your_api_key"
./run_full_ablation.sh
```

Smoke test a tiny subset before spending the full 1350 calls:

```bash
export OPENAI_API_KEY="your_api_key"
./10_run_exp1.sh --limit 3
./11_run_exp2_safety.sh --limit 2
./12_extract_results.sh
./13_statistics_results.sh
./14_make_result_figures.sh
```

Run by domain:

```bash
export OPENAI_API_KEY="your_api_key"
./10_run_exp1.sh --domain banking
./11_run_exp2_safety.sh --domain banking
./12_extract_results.sh
./13_statistics_results.sh
./14_make_result_figures.sh
```

Override sample size or benchmark version:

```bash
ABLATION_TASKS_PER_DOMAIN=10 AGENTDOJO_BENCHMARK_VERSION=v1.2.2 ./07_build_all.sh
```
