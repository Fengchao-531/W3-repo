# W3 Llama 3.1 Rerun

This folder contains a launcher for rerunning the W3 behavior experiments with
the same local Llama backend used by W3 TaskTracer:

```text
/scratch3/che489/FC-W2-SoK/model_cache/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
```

The launcher does not overwrite the existing GPT-4o outputs. It writes parallel
run directories under the model slug:

```text
local-llama-3.1-8b-instruct
```

## Smoke Test

```bash
cd /scratch3/che489/FC-W4/Tracing-Reproduction/W3
/scratch3/che489/.conda/envs/W4/bin/python XLLMs/run_w3_llama31.py --smoke --no-analyze
```

## Full Rerun

```bash
cd /scratch3/che489/FC-W4/Tracing-Reproduction/W3
/scratch3/che489/.conda/envs/W4/bin/python XLLMs/run_w3_llama31.py --experiment all
```

This runs:

- `Exp1_User_Context_Embedding`
- `Exp2_Task_Binding`
- `RQ2/Exp2_SafetyIntent`
- `RQ2/Exp3_ Controlled_Source-Provenance_Intervention`

After model runs finish, it calls each experiment's existing
process/statistics/figures functions.

## Useful Partial Runs

```bash
# One Exp1 job
/scratch3/che489/.conda/envs/W4/bin/python XLLMs/run_w3_llama31.py --experiment exp1 --limit 1 --no-analyze

# Exp2 only
/scratch3/che489/.conda/envs/W4/bin/python XLLMs/run_w3_llama31.py --experiment exp2

# RQ2 SafetyIntent, malicious arm only
/scratch3/che489/.conda/envs/W4/bin/python XLLMs/run_w3_llama31.py --experiment rq2-exp2 --arm malicious

# RQ2 controlled source, C1 only
/scratch3/che489/.conda/envs/W4/bin/python XLLMs/run_w3_llama31.py --experiment rq2-exp3 --condition C1
```

## Notes

- Default generation is deterministic: `temperature=0.0`, `do_sample=False`.
- Prompt rendering, Llama chat template handling, tool schema conversion, and
  tool-call parsing are imported from `Demo/01_local_llama31.py`.
- Prompts are not truncated. If a prompt exceeds `--max-input-tokens`, that run
  records an error rather than silently changing the input.
- Existing runs are skipped unless `--force` is passed.
- A launcher manifest is written to `XLLMs/llama31_run_manifest.json`.
