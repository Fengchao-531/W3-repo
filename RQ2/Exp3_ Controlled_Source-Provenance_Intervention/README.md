# RQ2 Exp3 Controlled Source-Provenance Intervention

Exp3 isolates source provenance as the only new RQ2 intervention:

```text
Content, timing, position, task, candidate set, and candidate order are held fixed.
C0 is an all-external baseline; C1 changes only M's source label; C2 changes only BM's source label.
```

Conditions:

```text
C0: M = external,      BM = external,      BW = external
C1: M = user-provided, BM = external,      BW = external
C2: M = external,      BM = user-provided, BW = external
```

Run count:

```text
180 pairs x 3 conditions = 540 runs
```

No separate instrumented questionnaire/record_decision run is generated. RQ2 mechanism evidence is produced from natural trace analysis after the controlled source experiment.

Primary causal estimands:

```text
M source effect  = C1 - C0
BM source effect = C2 - C0
```

C1 vs C2 is retained only as a descriptive contrast, not as the main causal claim.

Main files:

```text
00_config/       experiment config and source conditions
01_manifest/     Exp3 pairs, run manifest, run queue, validation
02_controlled_source/raw_runs/
04_processed/    run-level, pair-level, candidate-level, transition tables
05_statistics/   source-effect, McNemar, bootstrap, trace summaries
06_figures/      controlled source and propagation figures
07_validation/   manifest and source-intervention QC
```

Build and validate:

```bash
./01_build_dataset.sh
./02_validate_dataset.sh
./03_make_run_queue.sh
```

Shell entrypoints use the same Python convention as Exp1/Exp2:

```bash
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
```

Model runs require an OpenAI API key available to AgentDojo. The runner first checks `OPENAI_API_KEY`; if absent, it looks for a non-empty `OPENAI_API_KEY` in Codex `auth.json` without printing it.

Smoke runs:

```bash
./04_run_exp3.sh --limit 6
```

Full runs:

```bash
./04_run_exp3.sh
```

Process completed runs:

```bash
./run_analysis.sh
```

The runner reuses the Exp1 AgentDojo suite, task environment, model defaults, candidate construction, and frozen candidate order. Exp3 provides a synchronized candidate observation before action so exposure is fixed at 1.

Primary outputs after `./run_analysis.sh`:

```text
05_statistics/00_primary_source_effect.csv
05_statistics/01_mcnemar_results.csv
05_statistics/02_cluster_bootstrap.csv
05_statistics/03_trace_analysis_results.csv
05_statistics/05_c1_c2_descriptive_contrast.csv
```
