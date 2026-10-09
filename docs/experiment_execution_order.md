# Experiment Execution Order

Run commands from the repository root after installing the dependencies in
[installation.md](installation.md) and configuring the selected model backends.

## 0. Task, artifact, and model setup

- Tasks: AgentDojo travel, workspace, banking, and slack suites.
- Matched configuration: base task, benefit dimension, carrier, candidate set,
  candidate order, source condition, and artifact target.
- Candidate types: M, BM, BW, configured by src/source_relocation/spec.py.
- Experimental engine: src/source_relocation/agent.py.
- Metrics: src/source_relocation/statistics.py and evaluation.py.

```bash
source-relocation build --domain travel --manifest outputs/manifests/travel.jsonl
```

The default travel design uses 20 base tasks × 3 benefit dimensions ×
3 carrier variants, yielding 180 configurations per condition.

## 1. RQ1: Source-relocation behavior and controls

| Order | Experiment | Contrast | Execution |
| --- | --- | --- | --- |
| 1.1 | Exp1 relocation | E / UC_M / UC_BM | experiments/rq1/relocation.py |
| 1.2 | Exp2 position | beginning / middle / end for M and BM | experiments/rq1/position.py |
| 1.3 | Exp3 preference | R+D vs R+P+D for M and BM | experiments/rq1/preference.py |
| 1.4 | Exp4 instruction | UC+P vs UC+P+I | experiments/rq1/instruction.py |
| 1.5 | Exp5 reliability | E / E+V and UC / UC+V | experiments/rq1/reliability.py |
| 1.6 | Source label | textual external vs user-provided attribution | experiments/rq1/source_label.py |
| 1.7 | Matched statistical analysis | paired adoption rate differences and task-cluster CI | analysis/rq1_controls.py |
| 1.8 | Joint utility and paired candidate switches | adoption with task completion; E to UC selection changes | analysis/rq1_joint.py |

```bash
python reproduction/reproduce_rq1.py --model gpt4o --domain travel
python analysis/rq1_controls.py --runs outputs/runs/rq1
python analysis/rq1_joint.py --runs outputs/runs/rq1/relocation
```

The RQ1 runner executes all six experiments and produces source-condition
summaries and matched comparison estimates.

## 2. RQ2: Post-exposure internal processing

| Order | Experiment | Entry point | Output |
| --- | --- | --- | --- |
| 2.0 | Initial exposure, first-observation step, mention, plan and action | analysis/rq2_exposure.py | rq2_exposure.csv |
| 2.1 | Extract matched E/UC decision contexts | reproduction/build_contexts.py | contexts.jsonl |
| 2.2 | Layer-wise target-code support | CLI internal representation | representation.jsonl |
| 2.3 | Split selection and held-out checkpoints | reproduction/reproduce_rq2.py | discovery_contexts.jsonl; heldout_contexts.jsonl |
| 2.4 | Attention and MLP layer sweeps | CLI internal sweep | sweep.jsonl |
| 2.5 | Head-level interventions | CLI internal heads | head_discovery.jsonl |
| 2.6 | Top-3 and counteracting head selection | analysis/rq2_heads.py | selected_heads.json |
| 2.7 | Top-3 / counteracting / Random3 / FullWindow | CLI internal headsets | heldout_headsets.jsonl |
| 2.8 | Semantic-region attention | CLI internal attention | attention.jsonl |
| 2.9 | Region length and artifact-share normalization | analysis/rq2_regions.py | semantic_regions.csv |
| 2.10 | M vs BM and code-string controls | CLI internal representation / code_control | representation.jsonl; code_control.jsonl |
| 2.11 | Separate Exp5 reliability attention | build_contexts.py --experiment reliability; CLI internal attention | reliability_attention.jsonl |
| 2.12 | Reliability-region normalization | analysis/rq2_regions.py | reliability_regions.csv |

```bash
python analysis/rq2_exposure.py --manifest outputs/manifests/travel.jsonl \
  --runs outputs/runs/rq1/relocation --out outputs/analysis/rq2_exposure.csv

python reproduction/build_contexts.py --manifest outputs/manifests/travel.jsonl \
  --model gpt4o --experiment relocation --out outputs/internal/travel_contexts.jsonl

python reproduction/build_contexts.py --manifest outputs/manifests/travel.jsonl \
  --model gpt4o --experiment reliability --out outputs/internal/travel_reliability_contexts.jsonl

python reproduction/reproduce_rq2.py \
  --model llama31 --contexts outputs/internal/travel_contexts.jsonl \
  --reliability-contexts outputs/internal/travel_reliability_contexts.jsonl \
  --outdir outputs/internal/llama31 --sweep-first 20 --sweep-last 32 \
  --window-first 25 --window-last 28
```

Other open-weight models use their checkpoint-specific layer ranges and
head counts from configs/models and docs/model_configuration.md. The default
RQ2 split selects nine matched M units and nine matched BM units for head
discovery, with remaining eligible units used for held-out evaluation.

## 3. RQ3: Defense evaluation, safety guidance, and deployed agents

| Order | Experiment | Entry point | Output |
| --- | --- | --- | --- |
| 3.1 | H1 no guidance, H2 soft, H3 explicit verification | experiments/rq3/verification.py | JSON trajectories and outcomes |
| 3.2 | E/UC × M/BM with no defense | experiments/rq3/defenses.py --defense none | JSON trajectories and outcomes |
| 3.3 | Sandwich | --defense sandwich | defense events and outcomes |
| 3.4 | StruQ | --defense struq | defense events and outcomes |
| 3.5 | SecAlign | --defense secalign | defense events and outcomes |
| 3.6 | Perplexity | --defense perplexity | defense events and outcomes |
| 3.7 | DataSentinel | --defense datasentinel | defense events and outcomes |
| 3.8 | CausalArmor | --defense causalarmor | defense events and outcomes |
| 3.9 | Matched attack, task and safe-completion statistics | analysis/rq3_results.py | rates and paired CI |
| 3.10 | Browser-based deployed response collection | reproduction/deployed_capture.py | observations.jsonl |
| 3.11 | Six-constraint annotation records | reproduction/deployed_capture.py --annotation-template | annotated.jsonl |
| 3.12 | Deployed service constraint scoring | source-relocation deployed | deployed.csv |

```bash
python reproduction/reproduce_rq3.py --model gpt4o --domain travel --defense datasentinel
python analysis/rq3_results.py
pip install -e '.[browser]'
python -m playwright install chromium
python reproduction/deployed_capture.py --agents configs/deployed_agents.json \
  --tasks data/tasks/deployed_travel.jsonl --out outputs/deployed/observations.jsonl
python reproduction/deployed_capture.py --out outputs/deployed/observations.jsonl \
  --annotation-template outputs/deployed/annotated.jsonl
source-relocation deployed --inputs outputs/deployed/annotated.jsonl \
  --out outputs/analysis/deployed.csv
```

Upstream defense installations and runtime configuration are in
[upstream_defenses.md](upstream_defenses.md). The browser collector accepts a JSON array of agent configurations, each containing
`name`, `url`, `input_selector`, `response_selector`, and optionally
`submit_selector`, `storage_state`, and `timeout_ms`. The task file contains
`task_id` and `prompt`. The six applicability and violation annotations
are defined in deployed_agent_schema.md and are supplied in the annotated
records before aggregation.

## 4. End-to-end entry point and figures

```bash
python reproduction/reproduce_all.py --print-commands
python reproduction/reproduce_all.py --rq1-model gpt4o \
  --rq2-model llama31 --rq3-model gpt4o --domain travel
python reproduction/reproduce_figures.py --rq2-input \
  outputs/internal/llama31/representation.jsonl
python reproduction/reproduce_tables.py
```

RQ1 figures are created by plotting/rq1_figures.py. RQ2 layer-gap and
intervention charts use plotting/rq2_figures.py. RQ3 action-rate plots use
plotting/rq3_figures.py. The tabular statistics are generated by
analysis/rq1_controls.py, analysis/rq2.py, analysis/rq2_heads.py,
analysis/rq2_regions.py, and analysis/rq3_results.py.


## Cross-model execution

Behavioral model aliases: `gpt4o`, `claude35`, `gemini25`, `llama31`, `qwen`, `gemma`, `mistral`, and `deepseek`. Internal tracing uses the five open-weight models.

```bash
python reproduction/reproduce_rq1.py --models all --domain travel
python reproduction/reproduce_rq3.py --models qwen,gemma,llama31 --domain travel --defense none
python reproduction/reproduce_rq2.py --models all --contexts outputs/internal/travel_contexts.jsonl --outdir outputs/internal
python reproduction/reproduce_all.py --rq1-models all --rq2-models all --rq3-models all --print-commands
```

Each behavioral trajectory is organized by experiment, model, source condition, defense, and matched task–artifact identifier. RQ2 internal records are organized by model and matched unit.

## Outcome review

```bash
python reproduction/review_trajectories.py --runs outputs/runs --template outputs/audit/review_template.csv
python reproduction/review_trajectories.py --runs outputs/runs --annotations outputs/audit/review_template.csv --out outputs/audit/audited_results.jsonl
```

See [Behavior Annotation](behavior_annotation.md) for exposure, mention, planning, candidate selection, confirmed tool execution, original-task utility and safe-completion criteria.
