# Exp4b E0 Run Notes

## Does Any Previous Condition Already Satisfy E0?

No.

The closest previous condition is Exp1 `E`, but Exp1 `E` uses the desire-extended prompt:

`original task + general preference`

Therefore Exp1 `E` is an external condition with general preference still present. It is not the requested no-preference external baseline.

The existing Exp4 `A0` does satisfy:

`UC artifact + no general preference + no binding`

The missing condition is:

`E0 = external artifact + no general preference + no binding`

## New Condition

The new condition is implemented as:

`Exp4b_Preference_Controlled_External_Baseline`

For each existing Exp4 `A0` matched unit:

- same `pair_id`
- same base task
- same target malicious artifact
- same carrier type
- same candidate set and candidate order
- no general preference
- no explicit binding
- artifact removed from the initial user message
- artifact available through the external offer tools

## Key Comparison

The primary paired contrast is:

`A0 - E0`

This tests whether the user-context effect persists after removing both general preference and explicit binding.

## Submitted Jobs

Submitted on 2026-10-01:

- `35284801`: `Exp4bE0-1`, Gemma then Qwen
- `35284802`: `Exp4bE0-2`, Mistral
- `35284803`: `Exp4bE0-3`, Llama3.1 then DeepSeek

Progress command:

```bash
cd /scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs
./progress_exp4b_e0.sh
```

## Expected Output Per Model

Each model writes:

- `Exp4b_Preference_Controlled_External_Baseline/04_processed/00_E0_run_level_results.csv`
- `Exp4b_Preference_Controlled_External_Baseline/04_processed/02_E0_A0_combined_run_level.csv`
- `Exp4b_Preference_Controlled_External_Baseline/05_statistics/00_primary_E0_A0.csv`
- `Exp4b_Preference_Controlled_External_Baseline/05_statistics/01_paired_E0_vs_A0.csv`
