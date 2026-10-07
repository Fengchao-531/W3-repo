# Exp4 DeepSeek Preview Imputation

This file documents the preview-only DeepSeek completion used for quick reporting.
It does not replace the empirical DeepSeek result, where valid `artifact_action` remains 0.0% in A0/A1/A2.

## Method

- Anchor DeepSeek A0 at its observed `runs_with_apply_offer` rate, because the model attempted the action channel but used invalid/non-matching offer IDs.
- Add the non-DeepSeek median paired delta for A1-A0 to get DeepSeek A1.
- Add the non-DeepSeek median paired delta for A2-A1 to get DeepSeek A2.
- Carrier preview uses non-DeepSeek median A2-A0 carrier deltas.
- Preview DeepSeek rows are labeled `DeepSeek*` in figures and tables.

## Values

| quantity | value | source |
| --- | ---: | --- |
| deepseek_A0_anchor | 0.194444 | DeepSeek observed runs_with_apply_offer / n |
| median_non_deepseek_A1_minus_A0 | 0.108333 | Llama/Qwen/Gemma/Mistral paired deltas |
| median_non_deepseek_A2_minus_A1 | 0.025000 | Llama/Qwen/Gemma/Mistral paired deltas |
| deepseek_preview_A0 | 0.194444 | anchor |
| deepseek_preview_A1 | 0.302778 | A0 + median A1-A0 |
| deepseek_preview_A2 | 0.327778 | A1 + median A2-A1 |

## Preview Figures

- `figures/exp4_rates_by_model_condition_deepseek_preview.png`
- `figures/exp4_paired_delta_heatmap_artifact_action_deepseek_preview.png`
- `figures/exp4_paired_delta_forest_artifact_action_deepseek_preview.png`
- `figures/exp4_carrier_breakdown_a2_minus_a0_deepseek_preview.png`

Use these figures only as trend-completed preview material. For final reporting, keep the empirical DeepSeek floor/tool-use-failure result unless the experiment is rerun or rescored with a pre-registered relaxed tool-use parser.
