# RQ2 Exp2 Safety Intent

Incremental experiment over Exp1. H1 is reused from frozen Exp1 `UC_M`; this folder only generates and runs new H2/H3 safety-intent variants.

Core invariant:

```text
H2 = H1 + concern sentence
H3 = H2 + explicit verification sentence
```

No H1 model calls are generated. The default run queue contains only `UC_M` malicious-arm `condition in {H2,H3}`, so `N=180` gives `360` new runs.

The Exp1 `UC_B` snapshot is also frozen for provenance. To build the optional benign-control extension, set:

```bash
RQ2_INCLUDE_BENIGN_CONTROL=1 ./01_build_dataset.sh
```

Main files:

```text
00_exp1_reference/  immutable Exp1 H1 snapshots and checksums
01_dataset/         safety templates, verification metadata, H2/H3 manifest, run queue, validation report
02_runs/            H2/H3 trajectories after model execution
03_annotations/     initialized safety/security annotation tables
04_processed/       new-run results and matched H1-H2-H3 panels
```

Build and validate the dataset:

```bash
./01_build_dataset.sh
./02_validate_dataset.sh
./03_make_run_queue.sh
```

Run only a small smoke subset:

```bash
./04_run_exp2.sh --limit 4
```

Run all new H2/H3 conditions:

```bash
./04_run_exp2.sh
```

The runner reuses the Exp1 AgentDojo pipeline, system prompt, tools, candidate order, model defaults, and environment. It only changes the rendered user prompt by appending the RQ2 safety-intent sentence(s).

Process completed runs and generate statistics/figures:

```bash
./run_analysis.sh
```

Full pipeline:

```bash
export OPENAI_API_KEY="your_api_key"
./run_all.sh
```
