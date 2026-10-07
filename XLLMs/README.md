# XLLMs W3 Reruns

This folder contains open-weight rerun tooling for the W3 experiments.

The first target is the same model used by the TaskTracer work:

- `meta-llama/Llama-3.1-8B-Instruct`
- local snapshot: `/scratch3/che489/FC-W2-SoK/model_cache/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659`

Run a small smoke rerun first:

```bash
/scratch3/che489/.conda/envs/W4/bin/python \
  /scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/rerun_llama31_w3.py \
  --limit 1 --force
```

Run the current priority rerun (Exp1 E/UC core, then RQ2 Exp3):

```bash
/scratch3/che489/.conda/envs/W4/bin/python \
  /scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/rerun_llama31_w3.py \
  --force
```

By default the script creates an isolated experiment tree under:

`W3/XLLMs/Llama3.1`

The tree contains only the fixed experiment inputs plus new Llama outputs; GPT-4o
run outputs are not copied or overwritten.

Run both priority stages:

```bash
bash XLLMs/run_llama31_experiments.sh all
```

Run one priority stage:

```bash
bash XLLMs/run_llama31_experiments.sh exp1
bash XLLMs/run_llama31_experiments.sh exp3
```

The Exp1 stage runs only `E`, `UC_M`, and `UC_B`; `UC_B` is the repository
name for the requested `UC_BM` condition. `E_M` and `E_BM` are artifact-level
views of the same `E` behavior run. Exp2 Task Binding and RQ2 Safety H1/H2/H3
are intentionally excluded from `all`.

Each model call saves the exact serialized prompt and 32-layer prompt hidden
states under its experiment's `model_features` directory. After a successful
stage, `tracker_run_artifact_manifest.jsonl` is rebuilt at the Llama3.1 root
with artifact-level behavior labels and paths to prompts, traces, and hidden
states.
