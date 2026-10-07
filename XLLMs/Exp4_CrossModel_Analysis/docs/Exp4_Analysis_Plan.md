# Exp4 Analysis Plan

## Goal

Exp4 tests whether artifact action can remain elevated when general preference and explicit binding are removed, and whether general preference or explicit binding further changes artifact action.

## Conditions

- `A0`: artifact mention only; no general preference and no binding.
- `A1`: general preference plus artifact mention; no explicit binding.
- `A2`: general preference plus artifact mention plus explicit binding.

## Primary Readout

Use `artifact_action` as the main behavioral outcome.

Keep these as companion checks:

- `malicious_selected`
- `attack_success_human`
- `legitimate_utility`

## Required Tables

1. Data audit by model and condition.
2. Condition rates by model: A0, A1, A2.
3. Paired deltas by model:
   - `A1 - A0`: general-preference effect without binding.
   - `A2 - A1`: binding increment.
   - `A2 - A0`: full preference-plus-binding contrast.
4. McNemar transition counts and exact p-values.
5. Carrier-type robustness.
6. Task-level diagnostic table for artifact action.

## Required Figures

1. Artifact-action rates by model and condition.
2. Paired artifact-action delta heatmap.
3. Paired artifact-action delta forest plot with bootstrap confidence intervals.
4. Carrier-type breakdown for `A2 - A0`.

Only PNG figures are generated.

## Interpretation Rules

- Do not claim a universal monotonic ladder unless A0 < A1 < A2 holds consistently across models.
- Treat DeepSeek as a floor/tool-use-failure model because it never performs a valid artifact action in Exp4, despite seeing and considering the artifact.
- Treat A0 as the key preference-removal control: it tests whether artifact action can occur with neither general preference nor explicit binding.
- Treat `A1 - A0` as the general-preference amplification effect, not as evidence that binding is unnecessary.
- Treat `A2 - A1` as the binding increment, but report it as model-dependent.
- Do not claim that Exp4 fully explains the original UC-E gap unless a matched external no-preference condition, `E0`, is added.
- Use paired bootstrap CIs and McNemar tests as the main inferential checks.

## Current Recommended Claim

Exp4 shows that general task preferences can amplify artifact action, but they are not a necessary explanation for artifact action across models. Substantial artifact action remains even when both general preference and explicit artifact binding are removed, reaching 60.0% for Llama3.1, 33.3% for Qwen, and 20.6% for Mistral. General preference further increases artifact action for Llama3.1, Qwen, and Gemma, whereas the effect is absent or negative for Mistral and DeepSeek. Explicit binding provides no consistent additional increase across models.

## Remaining Preference-Confound Test

The current Exp4 conditions are all UC-side manipulations. Therefore Exp4 can show:

`artifact action can persist without preference or binding`.

It cannot by itself show:

`the UC-E gap persists after preference removal`.

The smallest additional condition is:

- `E0`: external artifact condition matched to A0, with no general preference and no explicit binding.

The key contrast would be:

`A0_UC - E0`.

If `E0 << A0`, the paper can say that removing general preference reduces or changes adoption but does not eliminate the user-context effect. If `E0 ~= A0`, the original UC-E difference should be reframed as substantially dependent on preference, task relevance, or interaction structure.
