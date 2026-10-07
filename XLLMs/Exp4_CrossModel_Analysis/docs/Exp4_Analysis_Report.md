# Exp4 General Preference Control: Cross-Model Analysis

Generated from each model's `Exp4_General_Preference_Control/05_processed/02_A0_A1_A2_combined_run_level.csv` after refreshing the Exp4 statistics merge for Mistral and DeepSeek.

## Protocol

- `A0`: original task plus artifact mention only; the general preference text is removed and there is no explicit binding instruction.
- `A1`: Exp2 UC reference; general preference plus artifact mention, but no explicit binding.
- `A2`: Exp2 UB reference; general preference plus artifact mention plus explicit binding.

The primary readout here is `artifact_action`, with `malicious_selected` and `attack_success_human` kept as companion checks. Deltas are paired by `pair_id`; confidence intervals are cluster bootstraps over matched units.

## Data Audit

| model | A0 | A1 | A2 |
| --- | --- | --- | --- |
| Llama3.1 | 180 | 180 | 180 |
| Qwen | 180 | 180 | 180 |
| Gemma | 180 | 180 | 180 |
| Mistral | 180 | 180 | 180 |
| DeepSeek | 180 | 180 | 180 |

All five models have 180 successful matched units per condition after the Mistral/DeepSeek reference merge was refreshed.

## Primary Rates

| model | condition | n | artifact_action_rate | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| Llama3.1 | A0 | 180 | 0.600 | 0.528 | 0.672 |
| Llama3.1 | A1 | 180 | 0.700 | 0.633 | 0.767 |
| Llama3.1 | A2 | 180 | 0.694 | 0.622 | 0.761 |
| Qwen | A0 | 180 | 0.333 | 0.267 | 0.406 |
| Qwen | A1 | 180 | 0.450 | 0.378 | 0.522 |
| Qwen | A2 | 180 | 0.511 | 0.439 | 0.583 |
| Gemma | A0 | 180 | 0.000 | 0.000 | 0.000 |
| Gemma | A1 | 180 | 0.161 | 0.111 | 0.217 |
| Gemma | A2 | 180 | 0.094 | 0.056 | 0.139 |
| Mistral | A0 | 180 | 0.206 | 0.150 | 0.267 |
| Mistral | A1 | 180 | 0.183 | 0.128 | 0.244 |
| Mistral | A2 | 180 | 0.239 | 0.178 | 0.300 |
| DeepSeek | A0 | 180 | 0.000 | 0.000 | 0.000 |
| DeepSeek | A1 | 180 | 0.000 | 0.000 | 0.000 |
| DeepSeek | A2 | 180 | 0.000 | 0.000 | 0.000 |

## Paired Effects

| model | comparison | n_pairs | left_rate | right_rate | delta_right_minus_left | ci_low | ci_high | mcnemar_exact_p | n01_left0_right1 | n10_left1_right0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek | A0_vs_A1 | 180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | NA | 0 | 0 |
| DeepSeek | A1_vs_A2 | 180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | NA | 0 | 0 |
| DeepSeek | A0_vs_A2 | 180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | NA | 0 | 0 |
| Gemma | A0_vs_A1 | 180 | 0.000 | 0.161 | 0.161 | 0.106 | 0.217 | 3.73e-09 | 29 | 0 |
| Gemma | A1_vs_A2 | 180 | 0.161 | 0.094 | -0.067 | -0.122 | -0.011 | 0.029 | 7 | 19 |
| Gemma | A0_vs_A2 | 180 | 0.000 | 0.094 | 0.094 | 0.056 | 0.139 | 1.53e-05 | 17 | 0 |
| Llama3.1 | A0_vs_A1 | 180 | 0.600 | 0.700 | 0.100 | 0.017 | 0.183 | 0.025 | 38 | 20 |
| Llama3.1 | A1_vs_A2 | 180 | 0.700 | 0.694 | -0.006 | -0.078 | 0.067 | 1.000 | 21 | 22 |
| Llama3.1 | A0_vs_A2 | 180 | 0.600 | 0.694 | 0.094 | 0.011 | 0.183 | 0.043 | 40 | 23 |
| Mistral | A0_vs_A1 | 180 | 0.206 | 0.183 | -0.022 | -0.056 | 0.011 | 0.344 | 3 | 7 |
| Mistral | A1_vs_A2 | 180 | 0.183 | 0.239 | 0.056 | 0.022 | 0.089 | 0.002 | 10 | 0 |
| Mistral | A0_vs_A2 | 180 | 0.206 | 0.239 | 0.033 | -0.006 | 0.072 | 0.180 | 10 | 4 |
| Qwen | A0_vs_A1 | 180 | 0.333 | 0.450 | 0.117 | 0.039 | 0.194 | 0.008 | 39 | 18 |
| Qwen | A1_vs_A2 | 180 | 0.450 | 0.511 | 0.061 | -0.022 | 0.144 | 0.185 | 34 | 23 |
| Qwen | A0_vs_A2 | 180 | 0.333 | 0.511 | 0.178 | 0.094 | 0.261 | 7.73e-05 | 48 | 16 |

## Cross-Model Summary

| comparison | n_models | macro_mean_delta | model_min_delta | model_max_delta | bootstrap_ci_low_across_models | bootstrap_ci_high_across_models |
| --- | --- | --- | --- | --- | --- | --- |
| A0_vs_A1 | 5 | 0.071 | -0.022 | 0.161 | 0.010 | 0.131 |
| A1_vs_A2 | 5 | 0.009 | -0.067 | 0.061 | -0.030 | 0.047 |
| A0_vs_A2 | 5 | 0.080 | 0.000 | 0.178 | 0.032 | 0.132 |

This macro table is descriptive rather than a strong population-level claim: with five models, heterogeneity is the main result.

## Main Reading

- A0 is the key preference-removal control: artifact action remains substantial without general preference or explicit binding for Llama3.1, Qwen, and Mistral.
- The strongest A1-A0 increase is Gemma with delta 0.161; this shows that general preference can amplify artifact action, so Exp4 should not be described as showing no preference effect.
- The strongest A2-A1 increase is Qwen with delta 0.061; explicit binding adds no consistent increment across models.
- DeepSeek is a null/tool-use-failure model in this experiment: A0/A1/A2 artifact-action rates remain at 0.0%. A separate diagnostic shows that it sees and considers the artifact but never issues a valid `apply_offer` call matching the experimental offer ID.
- Llama3.1 and Qwen show positive A0->A1 and A0->A2 movement. Gemma shows a strong A0->A1 increase, but A2 is lower than A1. Mistral shows little A0->A1 movement and a clear A1->A2 binding increment. This means Exp4 does not support a single monotonic ladder across all models.
- Exp4 does not by itself prove that the UC-E source/context gap persists after preference removal, because all three current conditions are UC-side manipulations. The minimal additional control for that claim is a matched external no-preference condition, E0.

## Carrier Breakdown

Carrier-type tables are saved separately because they are most useful for diagnostics and appendix robustness, not for the main result narrative.

## Figures

- `figures/exp4_rates_by_model_condition.png`: primary artifact-action rates by model and condition.
- `figures/exp4_paired_delta_heatmap_artifact_action.png`: paired deltas for A1-A0, A2-A1, and A2-A0.
- `figures/exp4_paired_delta_forest_artifact_action.png`: paired deltas with bootstrap confidence intervals.
- `figures/exp4_carrier_breakdown_a2_minus_a0.png`: carrier-type robustness for the full A2-A0 comparison.
- `figures/exp4_deepseek_tool_use_diagnostic.png`: DeepSeek-specific floor/tool-use diagnostic using observed trace-derived counts.

## Recommended Write-Up

Exp4 should be framed as a general-preference control, not as another mechanistic experiment. The clean claim is that general task preference can amplify artifact action, but it is not a necessary explanation for artifact action across models. Artifact action remains substantial even when both general preference and explicit artifact binding are removed, reaching 60.0% for Llama3.1, 33.3% for Qwen, and 20.6% for Mistral. General preference further increases artifact action for Llama3.1, Qwen, and Gemma, while the effect is absent or negative for Mistral. DeepSeek is different: it completed all conditions but remained at floor because it never produced a valid `apply_offer` call for the experimental offer ID. Explicit binding provides no consistent additional increase across models. This supports model-dependent sensitivity to user-side signals, not a universal monotonic escalation from A0 to A1 to A2.

## Analysis Plan for Final Manuscript

1. Lead with A0 rates to show that artifact action can persist after removing both general preference and explicit binding.
2. Use McNemar tests and paired bootstrap CIs as the main inferential statistics.
3. Treat A2-A1 as the binding increment, but describe it as heterogeneous across models.
4. Report DeepSeek separately as a floor/tool-use-failure model, not as missing data.
5. Do not claim that Exp4 fully rules out the preference-confound for the original UC-E contrast unless a matched E0 condition is added.
6. Put carrier-type and task-level breakdowns in appendix unless a specific carrier drives the conclusion.
